"""Tests for the placeholder-coordinate repair command.

The guarantees under test are the ones that keep this honest:

  * nothing is written without --apply;
  * a coordinate that already records a source is not touched;
  * a match that is not confidently the place is refused, not accepted;
  * anything outside Nepal is refused;
  * the Nominatim 1 request/second ceiling is enforced;
  * the identifying User-Agent is always sent.
"""
from __future__ import annotations

from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.test import TestCase

from tourist.geo_validation import NEPAL_LAT_MAX, NEPAL_LAT_MIN, NEPAL_LON_MAX, NEPAL_LON_MIN
from tourist.management.commands.geocode_placeholders import Geocoder
from tourist.models import Category, Destination, Hospital, PoliceStation


def response(rows, status=200):
    built = requests.Response()
    built.status_code = status
    import json

    built._content = json.dumps(rows).encode("utf-8")
    built.headers["Content-Type"] = "application/json"
    return built


class GeocoderTests(TestCase):
    def test_request_interval_floor_is_one_second(self):
        """Nominatim policy: absolute maximum 1 request per second."""
        slept = []
        clock = {"t": 0.0}

        def fake_sleep(seconds):
            slept.append(seconds)
            clock["t"] += seconds

        geocoder = Geocoder(
            "https://nominatim.example", min_interval=0.01, use_cache=False,
            sleep=fake_sleep, now=lambda: clock["t"],
        )
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])) as mocked:
            geocoder.search("one")
            clock["t"] += 100.0
            geocoder.search("two")
        self.assertEqual(slept, [], "no sleep needed when far apart in time")
        self.assertEqual(mocked.call_count, 2)

    def test_too_fast_calls_are_spaced(self):
        slept = []
        clock = {"t": 0.0}

        def fake_sleep(seconds):
            slept.append(seconds)
            clock["t"] += seconds

        geocoder = Geocoder(
            "https://nominatim.example", min_interval=1.1, use_cache=False,
            sleep=fake_sleep, now=lambda: clock["t"],
        )
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])):
            geocoder.search("one")
            geocoder.search("two")
        self.assertEqual(len(slept), 1)
        self.assertGreaterEqual(slept[0], 1.0)

    def test_configured_interval_below_policy_is_raised_to_one_second(self):
        geocoder = Geocoder("https://nominatim.example", min_interval=0.01)
        self.assertGreaterEqual(geocoder.min_interval, 1.0)

    def test_identifying_user_agent_is_always_sent(self):
        geocoder = Geocoder("https://nominatim.example", use_cache=False)
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])) as mocked:
            geocoder.search("Kathmandu")
        headers = mocked.call_args.kwargs["headers"]
        agent = headers.get("User-Agent", "")
        self.assertTrue(agent)
        self.assertNotIn("python-requests", agent.lower())
        self.assertIn("NepalYatra", agent)

    def test_results_are_cached(self):
        geocoder = Geocoder("https://nominatim.example", use_cache=True)
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])) as mocked:
            geocoder.search("Pokhara")
            geocoder.search("Pokhara")
        self.assertEqual(mocked.call_count, 1)


class GeocodePlaceholdersTests(TestCase):
    def setUp(self):
        # The command caches lookups, so each test must start from a clean
        # cache or a later test reads an earlier test's mocked response.
        from django.core.cache import cache

        cache.clear()
        self.category = Category.objects.create(name="Geocode Category")
        self.destination = Destination.objects.create(
            name="Siddhartha Municipality",
            slug="siddhartha-municipality",
            category=self.category,
            district="Kapilvastu",
            source="wikidata",
            external_id=7788,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
            latitude=Decimal("27.500000"),
            longitude=Decimal("83.500000"),
        )
        # Placeholder: exactly the destination's pin, no provenance.
        self.hospital = Hospital.objects.create(
            name="Kapilvastu District Hospital",
            address="Taulihawa",
            phone="",
            district="Kapilvastu",
            latitude=Decimal("27.500000"),
            longitude=Decimal("83.500000"),
            destination=self.destination,
        )
        self.good_match = [{
            "lat": "27.670000",
            "lon": "83.450000",
            "display_name": "Kapilvastu District Hospital, Taulihawa, Kapilvastu, Nepal",
            "name": "Kapilvastu District Hospital",
            "osm_type": "way",
            "osm_id": "12345",
        }]

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command("geocode_placeholders", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response(self.good_match)):
            output = self._run(limit=5)
        self.assertIn("DRY RUN", output)
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.latitude, Decimal("27.500000"))
        self.assertEqual(self.hospital.coordinate_source, "")

    def test_apply_records_real_coordinates_and_provenance(self):
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response(self.good_match)):
            self._run(limit=5, apply=True)
        self.hospital.refresh_from_db()
        self.assertEqual(str(self.hospital.latitude), "27.670000")
        self.assertEqual(str(self.hospital.longitude), "83.450000")
        self.assertIn("12345", self.hospital.coordinate_source)
        self.assertEqual(self.hospital.coordinate_status, "GEOCODED")
        self.assertIsNotNone(self.hospital.coordinate_retrieved_at)

    def test_unrelated_match_is_refused(self):
        """A hit in Nepal that does not mention the place is probably a centroid."""
        rows = [{
            "lat": "27.700000", "lon": "85.300000",
            "display_name": "Somewhere Else, Kathmandu, Nepal",
            "name": "Somewhere Else",
        }]
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response(rows)):
            self._run(limit=5, apply=True)
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.latitude, Decimal("27.500000"))
        self.assertEqual(self.hospital.coordinate_source, "")

    def test_match_outside_nepal_is_refused(self):
        rows = [{
            "lat": "27.670000", "lon": "95.000000",
            "display_name": "Kapilvastu District Hospital, Myanmar",
            "name": "Kapilvastu District Hospital",
        }]
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response(rows)):
            self._run(limit=5, apply=True)
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.latitude, Decimal("27.500000"))

    def test_no_match_leaves_the_row_alone(self):
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])):
            output = self._run(limit=5, apply=True)
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.latitude, Decimal("27.500000"))
        self.assertIn("no confident match", output)

    def test_already_provenanced_row_is_skipped(self):
        self.hospital.coordinate_source = "manual:field-survey"
        self.hospital.save(update_fields=["coordinate_source"])
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response(self.good_match)) as mocked:
            self._run(limit=5, apply=True)
        mocked.assert_not_called()
        self.hospital.refresh_from_db()
        self.assertEqual(self.hospital.coordinate_source, "manual:field-survey")

    def test_bulk_run_against_public_instance_warns(self):
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])):
            output = self._run(limit=200)
        self.assertIn("not intended for bulk geocoding", output)
        self.assertIn("your own Nominatim", output)

    def test_osm_attribution_is_printed(self):
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([])):
            output = self._run(limit=1)
        self.assertIn("OpenStreetMap contributors", output)

    def test_police_stations_are_included(self):
        station = PoliceStation.objects.create(
            name="Tauli Police Station",
            address="Taulihawa",
            phone="",
            latitude=Decimal("27.500000"),
            longitude=Decimal("83.500000"),
            destination=self.destination,
        )
        with patch("tourist.management.commands.geocode_placeholders.requests.get",
                   return_value=response([{
                       "lat": "27.480000", "lon": "83.460000",
                       "display_name": "Tauli Police Station, Kapilvastu, Nepal",
                       "name": "Tauli Police Station",
                       "osm_type": "node", "osm_id": "999",
                   }])):
            self._run(limit=5, apply=True)
        station.refresh_from_db()
        self.assertEqual(str(station.latitude), "27.480000")
        self.assertIn("999", station.coordinate_source)


class AuditProvenanceReportingTests(TestCase):
    """The audit must show the effect of the repair, or there is no way to
    tell whether a geocoding run helped."""

    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        category = Category.objects.create(name="Audit Category")
        self.destination = Destination.objects.create(
            name="Tauli", slug="tauli", category=category, district="Kapilvastu",
            source="wikidata", external_id=4242,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
            latitude=Decimal("27.500000"), longitude=Decimal("83.500000"),
        )
        self.placeholder = Hospital.objects.create(
            name="Placeholder Hospital", address="Taulihawa", phone="",
            district="Kapilvastu",
            latitude=Decimal("27.500000"), longitude=Decimal("83.500000"),
            destination=self.destination,
        )
        self.sourced = Hospital.objects.create(
            name="Sourced Hospital", address="Taulihawa", phone="",
            district="Kapilvastu",
            latitude=Decimal("27.610000"), longitude=Decimal("83.440000"),
            destination=self.destination,
            coordinate_source="nominatim.example#way/1",
            coordinate_status="GEOCODED",
        )

    def _audit(self, *args):
        out = StringIO()
        call_command("audit_coordinates", *args, stdout=out, stderr=out)
        return out.getvalue()

    def test_reports_provenance_coverage(self):
        output = self._audit()
        self.assertIn("without a recorded source", output)
        self.assertIn("1 without a recorded source, 1 sourced", output)

    def test_reports_coordinates_still_copied_from_the_parent(self):
        output = self._audit()
        self.assertIn("identical to its parent destination's pin: 1", output)
        self.assertIn("(0 of them now carry a source)", output)

    def test_audit_still_changes_nothing(self):
        before = list(Hospital.objects.values_list("id", "latitude", "longitude"))
        self._audit()
        after = list(Hospital.objects.values_list("id", "latitude", "longitude"))
        self.assertEqual(before, after)
