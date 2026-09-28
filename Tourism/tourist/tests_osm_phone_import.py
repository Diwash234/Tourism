"""Importing phone numbers from OpenStreetMap.

OSM is where this catalogue's hotel data came from -- its name tags match 100%
of the time -- and it holds 5,325 usable numbers for Nepal. That makes it the
one licensed source that can still close gaps. The licence is ODbL, so
attribution is recorded on every row written, and these tests check that too.

The rule most likely to cause harm is which candidate wins when several OSM
features share a name near one catalogue row, so that is pinned hardest here.
"""
import csv
import json
import os
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from tourist.management.commands.import_osm_phones import (
    Command, distance_km, normalise, osm_license_note,
)
from tourist.models import Category, Destination, Hospital, User


class NormaliseTests(SimpleTestCase):
    def test_filler_words_do_not_decide_a_match(self):
        self.assertEqual(normalise("Hotel Yak and Yeti"), normalise("Yak and Yeti"))
        self.assertEqual(normalise("The Dwarika's Hotel"), normalise("Dwarika's"))

    def test_a_name_kept_only_as_filler_still_compares(self):
        # Dropping every word would make all such names equal, so nothing is
        # dropped when that would leave nothing.
        self.assertEqual(normalise("Hotel"), "hotel")
        self.assertEqual(normalise("Hotel"), normalise("THE HOTEL"))

    def test_different_places_stay_different(self):
        self.assertNotEqual(normalise("Hotel Yak and Yeti"), normalise("Hotel Yak Splash"))


class DistanceTests(SimpleTestCase):
    def test_kathmandu_to_pokhara(self):
        km = distance_km(27.7172, 85.3245, 28.2096, 83.9856)
        self.assertGreater(km, 135)
        self.assertLess(km, 146)

    def test_zero_distance(self):
        self.assertAlmostEqual(distance_km(27.7, 85.3, 27.7, 85.3), 0.0, places=6)


class ChooseNearestTests(SimpleTestCase):
    """Which candidate wins, and when it refuses to pick."""

    def setUp(self):
        self.command = Command()
        self.near = {"phone": "014469064", "lat": 27.7172, "lon": 85.3245,
                     "name": "Bank", "osm_type": "node", "osm_id": 1}
        self.far = {"phone": "015971234", "lat": 27.7172, "lon": 85.3330,
                    "name": "Bank", "osm_type": "node", "osm_id": 2}

    def test_a_lone_candidate_is_used(self):
        best, why = self.command._choose([self.near], 27.7172, 85.3245, 3.0)
        self.assertIs(best, self.near)
        self.assertIn("km away", why)

    def test_the_clearly_nearest_candidate_wins(self):
        # Fifty metres away is this row's branch; the one two kilometres off is
        # a different branch that happens to share the name.
        best, why = self.command._choose([self.near, self.far], 27.7172, 85.3245, 3.0)
        self.assertIs(best, self.near)
        self.assertIn("nearest of", why)

    def test_two_candidates_almost_equally_close_are_refused(self):
        second = dict(self.far, lat=27.7172, lon=85.3250)  # ~45 m away
        best, why = self.command._choose([self.near, second], 27.7172, 85.3245, 3.0)
        self.assertIsNone(best)
        self.assertIn("none clearly nearest", why)

    def test_agreeing_candidates_near_each_other_are_accepted(self):
        # Two records, one number: that is corroboration, not disagreement.
        second = dict(self.far, phone="01-4469064", lat=27.7172, lon=85.3250)
        best, _why = self.command._choose([self.near, second], 27.7172, 85.3245, 3.0)
        self.assertIsNotNone(best)

    def test_nothing_within_the_radius_is_refused(self):
        best, why = self.command._choose([self.far], 27.7172, 85.3245, 0.5)
        self.assertIsNone(best)
        self.assertIn("no OSM feature within", why)

    def test_a_record_without_coordinates_cannot_be_matched(self):
        best, why = self.command._choose([self.near], None, None, 3.0)
        self.assertIsNone(best)
        self.assertIn("no coordinates", why)


class OdbLAttributionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("osm-qa@test.local", "OsmQA!123")
        category = Category.objects.create(name="OSM QA")
        self.destination = Destination.objects.create(
            name="Jiri", slug="jiri", category=category, description="A town.",
            latitude=27.5170, longitude=85.5200, created_by=self.user,
            status="approved", is_active=True)

    def _hospital(self, phone=""):
        return Hospital.objects.create(
            name="Jiri Hospital", address="Jiri", phone=phone,
            latitude=27.5170, longitude=85.5200,
            destination=self.destination, is_archived=False)

    def test_the_licence_is_named(self):
        self.assertIn("OpenStreetMap", osm_license_note())
        self.assertIn("ODbL", osm_license_note())

    def test_writing_a_number_records_the_odbl_credit(self):
        record = self._hospital()
        Command()._credit(record, {"phone": "014469064", "lat": 27.517,
                                   "lon": 85.520, "osm_type": "node", "osm_id": 42})
        record.refresh_from_db()
        # ODbL requires the credit to travel with the data, not just to exist in
        # a commit message.
        self.assertIn("OpenStreetMap", record.source_name or "")
        self.assertIn("openstreetmap.org", (record.source_url or "").lower())


class ImportCommandDryRunTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("osm-dry@test.local", "OsmDry!123")
        category = Category.objects.create(name="OSM Dry")
        self.destination = Destination.objects.create(
            name="Jiri", slug="jiri", category=category, description="A town.",
            latitude=27.5170, longitude=85.5200, created_by=self.user,
            status="approved", is_active=True)
        self.hospital = Hospital.objects.create(
            name="Jiri Hospital", address="Jiri", phone="",
            latitude=27.5170, longitude=85.5200,
            destination=self.destination, is_archived=False)

    def _run(self, *args, payload):
        """Run the command with Overpass replaced by a canned response."""
        original = Command._fetch
        Command._fetch = lambda self, k, v, attempts=4: payload
        self.addCleanup(lambda: setattr(Command, "_fetch", original))
        out = StringIO()
        call_command("import_osm_phones", *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def _payload(self, phone="014469064"):
        return [{"name": "Jiri Hospital", "phone": phone, "lat": 27.5170,
                 "lon": 85.5200, "osm_type": "node", "osm_id": 42}]

    def test_a_dry_run_writes_nothing(self):
        output = self._run(payload=self._payload())
        self.hospital.refresh_from_db()
        self.assertFalse((self.hospital.phone or "").strip())
        self.assertIn("DRY RUN", output)

    def test_apply_fills_a_gap(self):
        self._run("--apply", payload=self._payload())
        self.hospital.refresh_from_db()
        self.assertTrue((self.hospital.phone or "").strip())
        self.assertIn("OpenStreetMap", self.hospital.source_name or "")

    def test_a_number_already_on_record_is_never_replaced(self):
        self.hospital.phone = "015971234"
        self.hospital.save()
        self._run("--apply", payload=self._payload(phone="014469064"))
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.phone, "015971234")

    def test_templated_filler_is_treated_as_a_gap_not_a_number(self):
        self.hospital.phone = "037-520123"
        self.hospital.save()
        self._run("--apply", payload=self._payload())
        self.hospital.refresh_from_db()
        self.assertNotIn("520123", self.hospital.phone or "")

    def test_filler_in_the_source_is_not_imported(self):
        self._run("--apply", payload=self._payload(phone="037-520123"))
        self.hospital.refresh_from_db()
        self.assertFalse((self.hospital.phone or "").strip())

    def test_a_distinctive_number_the_source_does_not_agree_with_is_refused(self):
        far = [{"name": "Jiri Hospital", "phone": "014469064", "lat": 28.2096,
                "lon": 83.9856, "osm_type": "node", "osm_id": 1}]
        self._run("--apply", payload=far)
        self.hospital.refresh_from_db()
        self.assertFalse((self.hospital.phone or "").strip())
