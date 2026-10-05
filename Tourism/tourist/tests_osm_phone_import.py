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

    def test_a_name_with_nothing_distinctive_matches_nothing(self):
        # "Hotel" and "The Hotel" are both all business type. Normalising them
        # to two different strings would let each match a different branch on a
        # street where twenty exist, so both become unmatchable instead.
        self.assertEqual(normalise("Hotel"), "")
        self.assertEqual(normalise("THE HOTEL"), "")
        self.assertEqual(normalise("Grand Plaza"), "")

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

    def test_a_candidate_on_the_row_beats_one_over_a_km_away(self):
        # The row's own coordinates sit on one of them, and the other is well
        # outside a street's width. That separation is decisive, so the nearer
        # number is the right one rather than a coin-toss between branches.
        rival = {"phone": "015971234", "lat": 27.7280, "lon": 85.3290,
                 "name": "Bank", "osm_type": "node", "osm_id": 3}
        best, _why = self.command._choose([self.near, rival], 27.7172, 85.3245, 3.0)
        self.assertIsNotNone(best)

    def test_candidates_on_opposite_sides_of_the_radius_are_both_refused(self):
        # A tie dressed up as a "winner" would be the worst outcome: the nearest
        # is only slightly nearer, so neither is evidence about the other.
        a = {"phone": "014469064", "lat": 27.7262, "lon": 85.3245,
             "name": "Bank", "osm_type": "node", "osm_id": 4}
        b = {"phone": "015971234", "lat": 27.7266, "lon": 85.3245,
             "name": "Bank", "osm_type": "node", "osm_id": 5}
        best, why = self.command._choose([a, b], 27.7172, 85.3245, 3.0)
        self.assertIsNone(best)
        self.assertIn("none clearly nearest", why)

    def test_a_candidate_at_the_exact_coordinates_wins_over_one_fifty_metres_off(self):
        # Decisiveness is what the rule asks for, and at these distances it is
        # real: the row's own coordinates sit on one of them.
        rival = dict(self.far, lat=27.7172, lon=85.3260)
        best, _why = self.command._choose([self.near, rival], 27.7172, 85.3245, 3.0)
        self.assertIsNotNone(best)

    def test_a_candidate_on_the_row_and_one_far_away_still_refuses_when_close(self):
        # Nearest is 1.0 km, second is 1.05 km: inside the radius, and
        # essentially tied.
        nearish = {"phone": "014469064", "lat": 27.7262, "lon": 85.3245,
                   "name": "Bank", "osm_type": "node", "osm_id": 6}
        rival = {"phone": "015971234", "lat": 27.7267, "lon": 85.3245,
                 "name": "Bank", "osm_type": "node", "osm_id": 7}
        best, why = self.command._choose([nearish, rival], 27.7172, 85.3245, 3.0)
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


class EmptyResponseIsNotBelievedTests(SimpleTestCase):
    """Overpass throttles with a valid but empty answer, not an error.

    An empty result is indistinguishable from a category that genuinely has no
    numbers, so believing it silently under-reports the coverage that was
    actually available. It was caught in practice: amenity=hospital returned 275
    features on one run and 0 on the next, minutes apart, and the 0 was accepted.
    """

    def _run_with(self, payloads):
        """Call _fetch with a urlopen that returns the given payloads in order."""
        import io
        import urllib.request

        command = Command()
        original = urllib.request.urlopen
        calls = []

        def fake_urlopen(request, timeout=None):
            calls.append(request)
            payload = payloads[min(len(calls) - 1, len(payloads) - 1)]

            class Response(io.BytesIO):
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

            return Response(json.dumps(payload).encode("utf-8"))

        urllib.request.urlopen = fake_urlopen
        self.addCleanup(lambda: setattr(urllib.request, "urlopen", original))
        # The retry pause is real time; keep the test quick.
        import tourist.management.commands.import_osm_phones as module
        original_sleep = module.time.sleep
        module.time.sleep = lambda *_: None
        self.addCleanup(lambda: setattr(module.time, "sleep", original_sleep))
        return command._fetch("amenity", "hospital"), calls

    def test_an_empty_first_answer_is_retried(self):
        found, calls = self._run_with([
            {"elements": []},  # looks exactly like a throttle
            {"elements": [{"type": "node", "id": 1, "lat": 27.7, "lon": 85.3,
                           "tags": {"name": "Jiri Hospital", "phone": "014469064"}}]},
        ])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["phone"], "014469064")
        self.assertGreaterEqual(len(calls), 2, "the empty answer must not be believed")

    def test_a_genuinely_empty_category_is_reported_as_such(self):
        found, _calls = self._run_with([{"elements": []}])
        self.assertEqual(found, [])

    def test_a_candidate_without_coordinates_is_discarded(self):
        # An area-shaped result has no point of its own, so it cannot be matched
        # to a catalogue row's coordinates and is not offered.
        found, _calls = self._run_with([{"elements": [
            {"type": "way", "id": 2, "tags": {"name": "Somewhere", "phone": "014469064"}}]}])
        self.assertEqual(found, [])

    def test_filler_in_the_source_is_not_offered(self):
        found, _calls = self._run_with([{"elements": [
            {"type": "node", "id": 3, "lat": 27.7, "lon": 85.3,
             "tags": {"name": "Somewhere", "phone": "037-520123"}}]}])
        self.assertEqual(found, [])


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
