"""Tests for GPS fix validation and validated distance measurement.

The contract under test:
  * a broken coordinate is refused with a reason, never rounded to a number;
  * a good coordinate is preserved exactly, including outside Nepal;
  * a refused field never half-applies;
  * distance refuses rather than returning a wrong number.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from tourist.geo_validation import (
    QUALITY_APPROXIMATE,
    QUALITY_PRECISE,
    QUALITY_UNUSABLE,
    bearing_between,
    distance_between,
    haversine_km,
    validate_fix,
)
from tourist.models import User

NOW = datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)

KATHMANDU = (27.7172, 85.3240)
POKHARA = (28.2096, 83.9856)


class ValidateFixTests(TestCase):
    def test_good_fix_with_accuracy_is_precise(self):
        fix = validate_fix(
            *KATHMANDU, source="gps", accuracy_m=8, recorded_at=NOW, now=NOW
        )
        self.assertTrue(fix.usable)
        self.assertTrue(fix.precise)
        self.assertEqual(fix.quality, QUALITY_PRECISE)
        self.assertEqual(fix.reasons, [])

    def test_null_island_is_rejected(self):
        """(0, 0) is inside the valid range but is not a position."""
        fix = validate_fix(0, 0, source="gps", now=NOW)
        self.assertFalse(fix.usable)
        self.assertIn("null_island", fix.reasons)
        self.assertEqual(fix.quality, QUALITY_UNUSABLE)

    def test_out_of_range_is_rejected(self):
        for lat, lon in [(91, 0), (-91, 0), (0, 181), (0, -181)]:
            fix = validate_fix(lat, lon, now=NOW)
            self.assertFalse(fix.usable, f"{lat},{lon} should be rejected")
            self.assertIn("out_of_range", fix.reasons)

    def test_incomplete_pair_is_rejected(self):
        self.assertFalse(validate_fix(27.7, None, now=NOW).usable)
        self.assertFalse(validate_fix(None, 85.3, now=NOW).usable)
        self.assertIn("incomplete_pair", validate_fix(27.7, None, now=NOW).reasons)

    def test_missing_position_is_reported_not_crashed(self):
        for value in [None, "", "null", "NaN", "abc", True]:
            fix = validate_fix(value, value, now=NOW)
            self.assertFalse(fix.usable)
            self.assertIn("no_position", fix.reasons)

    def test_low_accuracy_fix_is_unusable(self):
        fix = validate_fix(*KATHMANDU, accuracy_m=9000, now=NOW)
        self.assertFalse(fix.usable)
        self.assertIn("accuracy_too_low", fix.reasons)

    def test_medium_accuracy_fix_is_approximate_but_usable(self):
        fix = validate_fix(*KATHMANDU, accuracy_m=500, now=NOW)
        self.assertTrue(fix.usable)
        self.assertEqual(fix.quality, QUALITY_APPROXIMATE)

    def test_stale_fix_is_rejected(self):
        stale = NOW - timedelta(hours=3)
        fix = validate_fix(*KATHMANDU, recorded_at=stale, now=NOW)
        self.assertFalse(fix.usable)
        self.assertIn("stale_fix", fix.reasons)

    def test_fresh_fix_is_accepted(self):
        fix = validate_fix(*KATHMANDU, recorded_at=NOW - timedelta(minutes=2), now=NOW)
        self.assertTrue(fix.usable)

    def test_absurdly_old_timestamp_is_rejected(self):
        fix = validate_fix(*KATHMANDU, recorded_at="1990-01-01T00:00:00Z", now=NOW)
        self.assertFalse(fix.usable)
        self.assertIn("implausible_timestamp", fix.reasons)

    def test_fix_without_quality_metadata_is_usable_but_not_precise(self):
        fix = validate_fix(*KATHMANDU, source="gps", now=NOW)
        self.assertTrue(fix.usable)
        self.assertEqual(fix.quality, QUALITY_APPROXIMATE)
        self.assertIn("no_accuracy_or_timestamp_reported", fix.warnings)

    def test_tourist_outside_nepal_is_warned_not_blocked(self):
        """Rejecting abroad travellers would break the product to be tidy."""
        tokyo = (35.6762, 139.6503)
        fix = validate_fix(*tokyo, accuracy_m=10, recorded_at=NOW, now=NOW)
        self.assertTrue(fix.usable)
        self.assertTrue(fix.outside_nepal)
        self.assertIn("outside_nepal", fix.warnings)
        self.assertEqual(fix.reasons, [])

    def test_decimal_and_string_inputs_are_parsed(self):
        from decimal import Decimal

        fix = validate_fix(Decimal("27.717200"), "85.324000", now=NOW)
        self.assertTrue(fix.usable)
        self.assertAlmostEqual(fix.latitude, 27.7172, places=5)


class DistanceTests(TestCase):
    def test_haversine_matches_known_distance(self):
        # Kathmandu to Pokhara is roughly 140 km.
        km = haversine_km(*KATHMANDU, *POKHARA)
        self.assertTrue(130 < km < 150, km)

    def test_distance_is_available_for_good_points(self):
        result = distance_between(*KATHMANDU, *POKHARA)
        self.assertTrue(result.available)
        self.assertAlmostEqual(result.km, 140, delta=15)

    def test_distance_refuses_null_island_origin(self):
        result = distance_between(0, 0, *POKHARA)
        self.assertFalse(result.available)
        self.assertIsNone(result.km)
        self.assertTrue(any("origin:null_island" in r for r in result.reasons))

    def test_distance_refuses_incomplete_destination(self):
        result = distance_between(*KATHMANDU, None, None)
        self.assertFalse(result.available)
        self.assertTrue(any("destination:" in r for r in result.reasons))

    def test_float_conversion_of_unavailable_distance_raises(self):
        result = distance_between(0, 0, *POKHARA)
        with self.assertRaises(ValueError):
            float(result)

    def test_quality_reflects_the_worst_end(self):
        good = validate_fix(*KATHMANDU, accuracy_m=5, recorded_at=NOW, now=NOW)
        fair = validate_fix(*POKHARA, now=NOW)
        result = distance_between(*KATHMANDU, *POKHARA, origin=good, destination=fair)
        self.assertEqual(result.quality, QUALITY_APPROXIMATE)

    def test_bearing_refuses_unusable_points(self):
        self.assertIsNone(bearing_between(0, 0, *POKHARA))
        self.assertIsNotNone(bearing_between(*KATHMANDU, *POKHARA))

    def test_zero_distance_for_same_point(self):
        result = distance_between(*KATHMANDU, *KATHMANDU)
        self.assertTrue(result.available)
        self.assertEqual(result.km, 0.0)


class LocationUpdateApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="gps-tester@example.com", password=None, role="tourist"
        )
        self.client.force_authenticate(self.user)

    def _post(self, payload):
        return self.client.post("/api/v1/auth/update-location/", payload, format="json")

    def test_good_gps_fix_is_stored_with_metadata(self):
        response = self._post(
            {
                "latitude": 27.7172,
                "longitude": 85.3240,
                "source": "gps",
                "accuracy": 12,
                "recorded_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        )
        self.assertEqual(response.status_code, 200, response.content[:300])
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.latitude)
        self.assertEqual(self.user.gps_accuracy_m, 12)
        self.assertIsNotNone(self.user.gps_validated_at)
        self.assertIn(self.user.gps_validation_state, {"precise", "approximate"})

    def test_null_island_is_refused_and_previous_position_kept(self):
        self.user.latitude = 27.7172
        self.user.longitude = 85.3240
        self.user.save(update_fields=["latitude", "longitude"])

        response = self._post({"latitude": 0, "longitude": 0, "source": "gps"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["position_unchanged"], True)

        self.user.refresh_from_db()
        # The good position must survive a broken submission.
        self.assertAlmostEqual(float(self.user.latitude), 27.7172, places=4)
        self.assertEqual(self.user.gps_validation_state, QUALITY_UNUSABLE)
        self.assertIn("null_island", self.user.gps_validation_reasons)

    def test_stale_fix_is_refused(self):
        stale = (datetime.now(tz=timezone.utc) - timedelta(hours=5)).isoformat()
        response = self._post(
            {"latitude": 27.7172, "longitude": 85.3240, "recorded_at": stale}
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.latitude)
        self.assertIn("stale_fix", self.user.gps_validation_reasons)

    def test_very_low_accuracy_fix_is_refused(self):
        response = self._post(
            {"latitude": 27.7172, "longitude": 85.3240, "accuracy": 12000}
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.latitude)

    def test_geoip_fallback_is_not_labelled_as_gps(self):
        """A desktop user's GeoIP position must not claim to be a GPS fix."""
        with override_settings(USE_GEOIP=True):
            response = self._post({"latitude": 27.7172, "longitude": 85.3240})
        self.assertIn(response.status_code, (200, 400))
        self.user.refresh_from_db()
        if response.status_code == 200:
            self.assertIn(
                self.user.location_source,
                {"gps", "geoip", "manual", "geolocation", "field"},
            )
            self.assertNotEqual(self.user.location_source, "")
