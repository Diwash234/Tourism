"""Repairing photographs that are attached to places they do not show.

The library shipped with 796 image URLs attached to more than one destination,
covering 19,791 of 20,168 real image rows: one SAARC Secretariat photograph on
331 destinations, one of Patan Durbar Square on 236. Only 377 rows were
attached to exactly one place, so true coverage was 2.6%.

These tests reproduce that defect in miniature and pin the repair: a photograph
that names a place is re-pointed to it, and one that names no single place is
removed from every destination rather than left to misrepresent them.
"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from tourist.models import Category, Destination, DestinationImage, User

PHOTO_OF_PATAN = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Patan_durbar_square.jpg"
PHOTO_OF_TAISEK = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Taumadi_square.jpg"


class MisattributedPhotoRepairTests(TestCase):
    def setUp(self):
        user = User.objects.create_superuser("repair-qa@test.local", "RepairQA!123")
        category = Category.objects.create(name="Repair QA")
        self.patan = Destination.objects.create(
            name="Patan Durbar Square", slug="patan-durbar-square", category=category,
            description="A real courtyard in Patan.", latitude=27.6727, longitude=85.3250,
            created_by=user, status="approved", is_active=True)
        self.pokhara = Destination.objects.create(
            name="Pokhara", slug="pokhara", category=category,
            description="A city in the hills.", latitude=28.2096, longitude=83.9856,
            created_by=user, status="approved", is_active=True)
        self.bhairahawa = Destination.objects.create(
            name="Bhairahawa", slug="bhairahawa", category=category,
            description="A city in the Terai.", latitude=27.6700, longitude=83.4400,
            created_by=user, status="approved", is_active=True)

    def _image(self, destination, url):
        return DestinationImage.objects.create(
            destination=destination, external_url=url, caption="photo",
            copyright_status="verified_reusable", verification_status="approved",
            is_verified=True, source_platform="wikimedia",
        )

    def _report(self, **kwargs):
        out = StringIO()
        call_command("repair_misattributed_photos", "--report-only", stdout=out, **kwargs)
        return out.getvalue()

    def test_photo_naming_a_place_is_repointed_to_it(self):
        # The same photograph is sitting on three unrelated destinations.
        for destination in (self.pokhara, self.bhairahawa, self.patan):
            self._image(destination, PHOTO_OF_PATAN)

        call_command("repair_misattributed_photos", stdout=StringIO())

        self.assertEqual(
            DestinationImage.objects.filter(external_url=PHOTO_OF_PATAN).count(), 1,
            "a photograph of one place must not stay on three")
        keeper = DestinationImage.objects.get(external_url=PHOTO_OF_PATAN)
        self.assertEqual(keeper.destination_id, self.patan.id,
                         "it should remain only on the place it actually shows")
        # The destinations that lost the wrong photo are not left with a
        # dangling cover pointing at a picture of somewhere else.
        for destination in (self.pokhara, self.bhairahawa):
            self.assertFalse(
                DestinationImage.objects.filter(
                    destination=destination, external_url=PHOTO_OF_PATAN).exists())

    def test_photo_naming_no_place_is_removed_from_everyone(self):
        for destination in (self.pokhara, self.bhairahawa, self.patan):
            self._image(destination, PHOTO_OF_TAISEK)

        call_command("repair_misattributed_photos", stdout=StringIO())

        self.assertFalse(
            DestinationImage.objects.filter(external_url=PHOTO_OF_TAISEK).exists(),
            "a photograph that cannot be attributed to one place must not be "
            "presented as the photo of any of them")

    def test_report_only_changes_nothing(self):
        for destination in (self.pokhara, self.bhairahawa, self.patan):
            self._image(destination, PHOTO_OF_PATAN)

        before = DestinationImage.objects.count()
        output = self._report()

        self.assertEqual(DestinationImage.objects.count(), before)
        self.assertIn("REPORT ONLY", output)
        self.assertIn("misleading rows", output)

    def test_report_counts_the_misleading_rows(self):
        for destination in (self.pokhara, self.bhairahawa, self.patan):
            self._image(destination, PHOTO_OF_PATAN)
        output = self._report()
        self.assertIn("3", output)

    def test_unique_photos_are_never_touched(self):
        own = self._image(self.patan, "https://example.test/patan-own.jpg")
        call_command("repair_misattributed_photos", stdout=StringIO())
        self.assertTrue(DestinationImage.objects.filter(pk=own.pk).exists(),
                        "a photo used by exactly one destination is already correct")

    def test_database_with_no_sharing_is_a_clean_noop(self):
        self._image(self.patan, "https://example.test/only-one.jpg")
        out = StringIO()
        call_command("repair_misattributed_photos", stdout=out)
        self.assertIn("no image is attached to more than one", out.getvalue())
