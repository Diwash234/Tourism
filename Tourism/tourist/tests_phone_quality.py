"""Phone numbers must be real or absent -- never filler, never "nan".

Three defects arrived from the source CSVs and reached the public API:

* 788 of 801 police stations and 33 of 362 hospitals carried the literal text
  "nan" as their phone number, because a missing value was stringified rather
  than stored as NULL;
* 61 phone values kept a trailing ".0" from a float parse, and the national
  ones had also lost their trunk zero;
* the templated filler ("037-520123") that the original dataset used for
  unknown numbers.

These tests pin the classification, the repair, the storage cleanup and the
read-path guarantee.
"""
from django.apps import apps
from django.test import TestCase

from .models import Hospital, PoliceStation, User
from .phone_quality import (
    is_null_sentinel,
    is_placeholder_phone,
    is_unusable_phone,
    normalize_phone_artifact,
)
from .serializers import HospitalSerializer, PoliceStationSerializer, RestaurantSerializer


class NullSentinelTests(TestCase):
    def test_stringified_nulls_are_recognised(self):
        for value in ("nan", "NaN", "NAN", "none", "None", "null", "N/A", "n/a", "na", "-", "?"):
            with self.subTest(value=value):
                self.assertTrue(is_null_sentinel(value))

    def test_real_values_are_not_sentinels(self):
        for value in ("", None, "01-4469064", "+9779800000010", "nanotechnology"):
            with self.subTest(value=value):
                self.assertFalse(is_null_sentinel(value))


class PlaceholderPhoneTests(TestCase):
    def test_templated_filler_is_recognised(self):
        for value in ("037-520123", "089-420123", "025-560123", "87520123.0"):
            with self.subTest(value=value):
                self.assertTrue(is_placeholder_phone(value))

    def test_real_numbers_are_not_placeholders(self):
        for value in ("01-4469064", "061-454226", "+977 9746024466", ""):
            with self.subTest(value=value):
                self.assertFalse(is_placeholder_phone(value))


class PhoneRepairTests(TestCase):
    def test_national_landline_regains_its_trunk_zero(self):
        # 8 digits lost the leading trunk zero to the float parse.
        self.assertEqual(normalize_phone_artifact("14440000.0"), "014440000")
        self.assertEqual(normalize_phone_artifact("14377404.0"), "014377404")

    def test_international_number_gets_its_plus(self):
        self.assertEqual(normalize_phone_artifact("977014256656.0"), "+977014256656")

    def test_untouched_values_are_returned_unchanged(self):
        for value in ("01-4469064", "061-454226, 455949", "+977 9746024466;+977 984657294"):
            with self.subTest(value=value):
                self.assertEqual(normalize_phone_artifact(value), value)

    def test_sentinels_are_not_rewritten(self):
        # A sentinel is blanked by the caller, never turned into a number.
        self.assertEqual(normalize_phone_artifact("nan"), "nan")

    def test_unusable_covers_both_defects_but_not_repairable_numbers(self):
        self.assertTrue(is_unusable_phone("nan"))
        self.assertTrue(is_unusable_phone("037-520123"))
        self.assertFalse(is_unusable_phone("14440000.0"))
        self.assertFalse(is_unusable_phone("01-4469064"))


class _RecordingSchemaEditor:
    def __init__(self):
        self.statements = []

    def execute(self, statement, *args, **kwargs):
        self.statements.append(statement)


class _ServiceFixtures(TestCase):
    """Shared destination fixture; service rows hang off a Destination."""

    def setUp(self):
        from .models import Category, Destination

        user = User.objects.create_superuser("phone-fixture@test.local", "PhoneFix!123")
        category = Category.objects.create(name="Phone QA")
        self.destination = Destination.objects.create(
            name="Phone QA Destination", slug="phone-qa-destination", category=category,
            description="Fixture destination for phone-quality tests.",
            latitude=27.67, longitude=85.30, created_by=user,
        )

    def _police(self, name, phone):
        return PoliceStation.objects.create(
            destination=self.destination, name=name, address="QA Road", phone=phone,
            latitude=27.671, longitude=85.301,
        )

    def _hospital(self, name, phone):
        return Hospital.objects.create(
            destination=self.destination, name=name, address="QA Road", phone=phone,
            latitude=27.672, longitude=85.302, district="Kaski",
        )


class PhoneCleanupMigrationTests(_ServiceFixtures):
    """Migration 0086 fixes storage, not just the response."""

    def _run(self):
        from importlib import import_module

        module = import_module("tourist.migrations.0086_clean_phone_artifacts")
        editor = _RecordingSchemaEditor()
        module.clean(apps, editor)
        return editor

    def test_sentinels_and_filler_are_blanked(self):
        self._police("Nan Police", "nan")
        self._police("Templated Police", "037-520123")
        self._run()
        self.assertEqual(PoliceStation.objects.get(name="Nan Police").phone, "")
        self.assertEqual(PoliceStation.objects.get(name="Templated Police").phone, "")

    def test_float_mangled_real_numbers_are_repaired_not_dropped(self):
        self._police("Float Police", "14440000.0")
        self._hospital("Intl Hospital", "977014256656.0")
        self._run()
        self.assertEqual(PoliceStation.objects.get(name="Float Police").phone, "014440000")
        self.assertEqual(Hospital.objects.get(name="Intl Hospital").phone, "+977014256656")

    def test_real_numbers_survive_untouched(self):
        self._police("Real Police", "01-4469064")
        self._run()
        self.assertEqual(PoliceStation.objects.get(name="Real Police").phone, "01-4469064")

    def test_migration_is_idempotent(self):
        self._police("Idem Police", "14440000.0")
        self._run()
        self._run()
        self.assertEqual(PoliceStation.objects.get(name="Idem Police").phone, "014440000")

    def test_migration_reports_what_it_changed(self):
        # Planted with .update(), which bypasses the pre_save guard exactly as a
        # bulk import or raw-SQL load would. This is the case the migration
        # exists for: values written before the guard, or written by a path
        # that skips model signals.
        police = self._police("Reported Police", "01-4469064")
        PoliceStation.objects.filter(pk=police.pk).update(phone="nan")
        editor = self._run()
        self.assertTrue(editor.statements, "the migration should record what it cleaned")
        self.assertIn("PoliceStation", editor.statements[0])
        self.assertEqual(PoliceStation.objects.get(pk=police.pk).phone, "")


class PhoneWriteNormalisationTests(_ServiceFixtures):
    """Normalising on write closes the class of bug, not the instance.

    Migration 0086 cleaned what was stored and the read paths blank anything
    unusable, but several views assemble rows straight from model attributes.
    Patching every call site is repetitive and easy to miss on the next one, so
    a pre_save guard makes an unusable value unstorable in the first place.
    """

    def test_sentinel_cannot_be_saved(self):
        self._police("Saved Nan", "nan")
        self.assertEqual(PoliceStation.objects.get(name="Saved Nan").phone, "")

    def test_templated_filler_cannot_be_saved(self):
        self._police("Saved Filler", "037-520123")
        self.assertEqual(PoliceStation.objects.get(name="Saved Filler").phone, "")

    def test_float_mangled_is_repaired_on_save(self):
        self._police("Saved Float", "14440000.0")
        self.assertEqual(PoliceStation.objects.get(name="Saved Float").phone, "014440000")

    def test_real_number_is_preserved_on_save(self):
        self._police("Saved Real", "01-4469064")
        self.assertEqual(PoliceStation.objects.get(name="Saved Real").phone, "01-4469064")

    def test_hospital_is_guarded_too(self):
        self._hospital("Saved Hospital", "nan")
        self.assertEqual(Hospital.objects.get(name="Saved Hospital").phone, "")


class SerializerPhoneGuaranteeTests(_ServiceFixtures):
    """The read path is the last line of defence, for rows created later."""

    def test_nan_never_reaches_the_response(self):
        data = PoliceStationSerializer(self._police("PS nan", "nan")).data
        self.assertEqual(data["phone"], "")

    def test_templated_filler_never_reaches_the_response(self):
        data = PoliceStationSerializer(self._police("PS filler", "037-520123")).data
        self.assertEqual(data["phone"], "")

    def test_float_mangled_is_repaired_in_the_response(self):
        data = PoliceStationSerializer(self._police("PS float", "14440000.0")).data
        self.assertEqual(data["phone"], "014440000")

    def test_real_number_is_returned_verbatim(self):
        data = PoliceStationSerializer(self._police("PS real", "01-4469064")).data
        self.assertEqual(data["phone"], "01-4469064")

    def test_hospital_serializer_applies_the_same_guarantee(self):
        self.assertEqual(
            HospitalSerializer(self._hospital("Nan Hospital", "nan")).data["phone"], ""
        )

    def test_restaurant_serializer_applies_the_same_guarantee(self):
        from .models import Restaurant

        restaurant = Restaurant.objects.create(
            destination=self.destination, name="Nan Restaurant", description="QA",
            address="QA Road", phone="NaN", website="", opening_hours="", image_url="",
            latitude=27.673, longitude=85.303,
        )
        self.assertEqual(RestaurantSerializer(restaurant).data["phone"], "")
