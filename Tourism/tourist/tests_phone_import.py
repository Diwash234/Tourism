"""Filling missing phone numbers from the project's own source exports.

The catalogue held 1,620 usable numbers across 8,918 rows carrying a phone
field -- 18.2% coverage -- while 1,656 further numbers sat unused in the
repository's own CSV exports. These tests pin the rules that let those 1,656 in
without letting a wrong one in: a present number is never overwritten, a
sentence of English is never read as a number, and two records that disagree
are left alone rather than one of them being guessed at.
"""
import csv
import os
import tempfile

from django.core.management import call_command
from django.test import TestCase

from tourist.models import Category, Destination, Hotel, User
from tourist.management.commands.import_real_phones import (
    choose_number, distance_km, normalise, number_key, read_source_rows,
)
from tourist.phone_quality import usable_phone


class NormaliseTests(TestCase):
    def test_case_and_punctuation_do_not_matter(self):
        self.assertEqual(normalise("Hotel Harrison Palace"),
                         normalise("hotel  harrison, palace"))

    def test_absent_name_is_an_empty_key(self):
        self.assertEqual(normalise(None), "")
        self.assertEqual(normalise("   "), "")


class NumberKeyTests(TestCase):
    def test_punctuation_is_not_part_of_a_number_identity(self):
        # The hotel exports record one number twice, dashed and plain. Treating
        # those as two numbers made 1,573 hotels look ambiguous and withheld
        # numbers the sources had actually agreed on.
        self.assertEqual(number_key("+977-1-4479488"), number_key("+97714479488"))
        self.assertEqual(number_key("01-4469064"), number_key("014469064"))

    def test_genuinely_different_numbers_stay_different(self):
        self.assertNotEqual(number_key("+977-1-4479488"), number_key("+977-1-5171234"))


class DistanceTests(TestCase):
    def test_decimal_and_float_coordinates_interoperate(self):
        # latitude is Decimal on some models and float on others.
        from decimal import Decimal
        self.assertAlmostEqual(
            distance_km(Decimal("27.7172"), Decimal("85.3245"), 27.7172, 85.3245),
            0.0, places=6)

    def test_a_known_separation_is_reported(self):
        # Kathmandu to Pokhara is about 141 km. A flat approximation that treats
        # every degree as 111 km reports 158 km here, because a degree of
        # longitude is only 111 km at the equator and Nepal sits at 27 north.
        km = distance_km(27.7172, 85.3245, 28.2096, 83.9856)
        self.assertGreater(km, 135)
        self.assertLess(km, 146)

    def test_longitude_shrinks_towards_the_poles(self):
        # One degree of longitude at 27 N is about 99 km, not 111. Getting this
        # wrong let a record from the next district satisfy a 2 km test.
        km = distance_km(27.0, 85.0, 27.0, 86.0)
        self.assertGreater(km, 95)
        self.assertLess(km, 102)


class ChooseNumberTests(TestCase):
    def _candidate(self, phone, lat, lon, source="t.csv"):
        return {"phone": phone, "lat": lat, "lon": lon, "source": source}

    def test_a_nearby_record_supplies_the_number(self):
        chosen, source, why = choose_number(
            [self._candidate("014469064", 27.7172, 85.3245)], 27.7172, 85.3245, 2.0)
        self.assertEqual(chosen, "014469064")
        self.assertIn("km away", why)

    def test_a_distant_record_is_weaker_evidence_and_says_so(self):
        # Same name, 141 km away. The name fallback still applies when the name
        # resolves to exactly one number -- chain properties share a number
        # across branches -- but the reason string must not imply it was a
        # location match, because it was not.
        chosen, _, why = choose_number(
            [self._candidate("014469064", 27.7172, 85.3245)], 28.2096, 83.9856, 2.0)
        self.assertEqual(chosen, "014469064")
        self.assertIn("no source record was nearby", why)

    def test_a_nearby_record_beats_a_distant_one_of_the_same_name(self):
        # Proximity is the stronger evidence, so a disagreeing record 141 km
        # away does not veto the one at this destination's coordinates: that far
        # record is a different property that happens to share a name.
        chosen, _, why = choose_number(
            [self._candidate("014469064", 27.7172, 85.3245),
             self._candidate("015971234", 28.2096, 83.9856)],
            27.7172, 85.3245, 2.0)
        self.assertEqual(chosen, "014469064")
        self.assertIn("km away", why)

    def test_two_disagreeing_records_both_nearby_are_refused(self):
        # The case proximity cannot settle: same place, two numbers.
        chosen, _, why = choose_number(
            [self._candidate("014469064", 27.7172, 85.3245),
             self._candidate("015971234", 27.7180, 85.3250)],
            27.7172, 85.3245, 2.0)
        self.assertIsNone(chosen)
        self.assertIn("2 different numbers", why)

    def test_disagreeing_records_are_refused_not_guessed(self):
        chosen, _, why = choose_number(
            [self._candidate("014469064", 27.7172, 85.3245),
             self._candidate("015971234", 27.7180, 85.3250)],
            27.7172, 85.3245, 2.0)
        self.assertIsNone(chosen)
        self.assertIn("2 different numbers", why)

    def test_agreeing_records_in_two_formats_are_not_a_disagreement(self):
        chosen, _, _ = choose_number(
            [self._candidate("+977-1-4479488", 27.7048, 85.3180),
             self._candidate("+97714479488", 27.7048, 85.3180)],
            27.7048, 85.3180, 2.0)
        self.assertEqual(chosen, "+977-1-4479488")

    def test_an_unambiguous_name_is_used_when_no_location_is_known(self):
        chosen, _, why = choose_number(
            [self._candidate("014469064", None, None)], None, None, 2.0)
        self.assertEqual(chosen, "014469064")
        self.assertIn("unique number", why)

    def test_a_name_shared_by_several_numbers_is_refused(self):
        chosen, _, why = choose_number(
            [self._candidate("014469064", None, None),
             self._candidate("015971234", None, None)], None, None, 2.0)
        self.assertIsNone(chosen)
        self.assertIn("share this name", why)


class ReadSourceRowsTests(TestCase):
    """The reader is where a real number was silently lost before."""

    def _write_export(self, root, rows):
        """Write an export where the command actually looks for one."""
        directory = os.path.join(root, "Tourism", "dataset")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "hotel.csv")
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["Hotel Name", "Phone", "Latitude", "Longitude"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_english_missing_markers_are_not_read_as_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_export(tmp, [
                {"Hotel Name": "Real Place", "Phone": "014469064",
                 "Latitude": "27.7", "Longitude": "85.3"},
                {"Hotel Name": "Absent One", "Phone": "Not Available",
                 "Latitude": "27.7", "Longitude": "85.3"},
                {"Hotel Name": "Filler One", "Phone": "037-520123",
                 "Latitude": "27.7", "Longitude": "85.3"},
            ])
            index = read_source_rows(tmp)
        self.assertIn("real place", index)
        self.assertNotIn("absent one", index,
                         "'Not Available' fills 2,752 of 3,293 rows of the real export")
        self.assertNotIn("filler one", index)

    def test_only_usable_numbers_reach_the_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_export(tmp, [
                {"Hotel Name": "Kept", "Phone": "+977-1-4479488",
                 "Latitude": "27.7", "Longitude": "85.3"},
            ])
            index = read_source_rows(tmp)
        self.assertTrue(all(usable_phone(c["phone"]) for c in index["kept"]))


class ImportCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("phone-import@test.local", "ImportQA!123")
        category = Category.objects.create(name="Import QA")
        self.destination = Destination.objects.create(
            name="Kathmandu", slug="kathmandu", category=category,
            description="The valley.", latitude=27.7048, longitude=85.3180,
            created_by=self.user, status="approved", is_active=True)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # repository_root() anchors on ml_service/, and the exports are read from
        # Tourism/dataset/, so the fixture tree needs both directories present.
        os.makedirs(os.path.join(self.tmp.name, "ml_service"), exist_ok=True)
        dataset = os.path.join(self.tmp.name, "Tourism", "dataset")
        os.makedirs(dataset, exist_ok=True)
        with open(os.path.join(dataset, "hotel.csv"), "w",
                  encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["Hotel Name", "Phone", "Latitude", "Longitude"])
            writer.writeheader()
            writer.writerow({"Hotel Name": "Himalaya Lodge",
                             "Phone": "+977-1-4479488",
                             "Latitude": "27.7048", "Longitude": "85.3180"})
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.cwd)

    def _hotel(self, name, phone, lat=27.7048, lon=85.3180):
        return Hotel.objects.create(
            name=name, latitude=lat, longitude=lon, phone=phone,
            destination=self.destination, currency="NPR", booking_status="unknown",
            booking_url="", external_image_url="", facilities="", address="",
            source="test", source_url="", is_verified=True, is_active=True)

    def test_a_missing_number_is_filled_from_the_source(self):
        hotel = self._hotel("Himalaya Lodge", "")
        call_command("import_real_phones", "--apply", stdout=None)
        hotel.refresh_from_db()
        self.assertTrue(usable_phone(hotel.phone))

    def test_an_existing_number_is_never_overwritten(self):
        hotel = self._hotel("Himalaya Lodge", "0144699999")
        call_command("import_real_phones", "--apply", stdout=None)
        hotel.refresh_from_db()
        self.assertEqual(hotel.phone, "0144699999",
                         "a number already on record is better evidence than a file")

    def test_a_dry_run_changes_nothing(self):
        hotel = self._hotel("Himalaya Lodge", "")
        call_command("import_real_phones", stdout=None)
        hotel.refresh_from_db()
        self.assertFalse(usable_phone(hotel.phone))

    def test_running_twice_does_not_double_up(self):
        self._hotel("Himalaya Lodge", "")
        call_command("import_real_phones", "--apply", stdout=None)
        before = Hotel.objects.get(name="Himalaya Lodge").phone
        call_command("import_real_phones", "--apply", stdout=None)
        self.assertEqual(Hotel.objects.get(name="Himalaya Lodge").phone, before)

    def test_a_hotel_the_sources_do_not_mention_is_left_alone(self):
        hotel = self._hotel("Unrelated Guesthouse", "")
        call_command("import_real_phones", "--apply", stdout=None)
        hotel.refresh_from_db()
        self.assertFalse(usable_phone(hotel.phone),
                         "no source record means no evidence, not a guess")
