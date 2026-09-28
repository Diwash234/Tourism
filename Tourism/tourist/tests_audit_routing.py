"""Tests for the road-routing audit.

The check that earns its keep is the physical one: a road route cannot be
shorter than the straight line between the same two points. A provider that
returns a shorter "road distance" is not routing over roads, and every distance
in the app is then quietly wrong -- which is precisely the kind of failure that
looks fine in a screenshot.

The other property under test is that the audit never claims road-verified
routing on the strength of a number alone. It requires the engine label, the
status, and a physically consistent geometry.
"""
from __future__ import annotations

import json
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from tourist.geo_validation import haversine_km
from tourist.management.commands.audit_routing import (
    MAX_PLAUSIBLE_DETOUR,
    MIN_PLAUSIBLE_DETOUR,
    Probe,
    probe_pair,
)
from tourist.models import Category, Destination


class FakeDestination:
    def __init__(self, name, latitude, longitude):
        self.name = name
        self.latitude = None if latitude is None else Decimal(str(latitude))
        self.longitude = None if longitude is None else Decimal(str(longitude))


KTM = FakeDestination("Kathmandu Durbar Square", 27.7048, 85.3070)
POKHARA = FakeDestination("Phewa Lake", 28.2096, 83.9856)

# The real crow-flight distance between the two fixtures, so the payload a test
# returns lines up with what the audit independently recomputes.
TRUE_STRAIGHT_KM = haversine_km(27.7048, 85.3070, 28.2096, 83.9856)


def route_payload(distance_km, duration_min=180, engine="osrm_protocol_provider",
                  status="routed"):
    return {
        "straight_line_km": 140.0,
        "route_distance_km": distance_km,
        "road_distance_km": distance_km,
        "duration_min": duration_min,
        "status": status,
        "routing_engine": engine,
        "note": "Road metric supplied by the configured routing service.",
    }


class ProbeGeometryTests(TestCase):
    def test_a_plausible_road_route_is_verified(self):
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(225.0, 300)):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertEqual(probe.problems, [])
        self.assertTrue(probe.is_road_verified)
        self.assertGreater(probe.detour_ratio, MIN_PLAUSIBLE_DETOUR)

    def test_road_distance_shorter_than_the_straight_line_is_rejected(self):
        """Physically impossible. This is the failure the audit exists for."""
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(90.0)):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertFalse(probe.is_road_verified)
        self.assertTrue(any("shorter than" in p for p in probe.problems))

    def test_straight_line_echoed_back_is_rejected(self):
        """A route that only just exceeds the crow flight is not a road route."""
        echoed = round(TRUE_STRAIGHT_KM + 0.2, 2)
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(echoed)):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertFalse(probe.is_road_verified)
        self.assertTrue(any("echoing the straight-line" in p for p in probe.problems))

    def test_implausible_detour_is_rejected(self):
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(1000.0)):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertFalse(probe.is_road_verified)
        self.assertTrue(any("implausibly large" in p for p in probe.problems))

    def test_graph_fallback_is_never_road_verified(self):
        payload = route_payload(225.0, engine="graphml_fallback")
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=payload):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertFalse(probe.is_road_verified)
        self.assertTrue(any("corridor-estimate" in p for p in probe.problems))

    def test_unconfigured_provider_is_reported_not_verified(self):
        payload = {
            "straight_line_km": 140.0, "route_distance_km": None,
            "road_distance_km": None, "duration_min": None,
            "status": "routing_unconfigured", "routing_engine": None,
            "note": "No road-routing provider configured",
        }
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=payload):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertFalse(probe.is_road_verified)
        self.assertTrue(any("no road route returned" in p for p in probe.problems))

    def test_null_island_endpoint_is_refused(self):
        null = FakeDestination("Nowhere", 0, 0)
        with patch("tourist.management.commands.audit_routing.route_metrics") as mocked:
            probe = probe_pair(null, POKHARA, "bad")
        mocked.assert_not_called()
        self.assertFalse(probe.is_road_verified)
        self.assertTrue(any("no usable Nepal coordinate" in p for p in probe.problems))

    def test_out_of_nepal_endpoint_is_refused(self):
        delhi = FakeDestination("Delhi", 28.6139, 77.2090)
        with patch("tourist.management.commands.audit_routing.route_metrics") as mocked:
            probe = probe_pair(delhi, POKHARA, "bad")
        mocked.assert_not_called()
        self.assertFalse(probe.is_road_verified)

    def test_missing_coordinate_is_refused(self):
        blank = FakeDestination("Blank", None, None)
        with patch("tourist.management.commands.audit_routing.route_metrics") as mocked:
            probe = probe_pair(blank, POKHARA, "bad")
        mocked.assert_not_called()
        self.assertFalse(probe.is_road_verified)

    def test_real_world_kathmandu_pokhara_ratio_is_plausible(self):
        """Sanity bound on the threshold itself: the real road distance is
        roughly 225 km against ~140 km straight line, so the acceptance window
        has to admit it."""
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(225.0, 300)):
            probe = probe_pair(KTM, POKHARA, "kathmandu-pokhara")
        self.assertLess(probe.detour_ratio, MAX_PLAUSIBLE_DETOUR)
        self.assertGreater(probe.detour_ratio, MIN_PLAUSIBLE_DETOUR)


class RoutingAuditCommandTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        category = Category.objects.create(name="Routing Category")
        Destination.objects.create(
            name="Kathmandu Durbar Square", slug="kathmandu-durbar-square",
            category=category, district="Kathmandu", is_active=True,
            latitude=Decimal("27.7048"), longitude=Decimal("85.3070"),
        )
        Destination.objects.create(
            name="Phewa Lake", slug="phewa-lake", category=category, district="Kaski",
            is_active=True, latitude=Decimal("28.2096"), longitude=Decimal("83.9856"),
        )

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command("audit_routing", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def test_reports_not_verified_when_unconfigured(self):
        payload = {
            "straight_line_km": TRUE_STRAIGHT_KM, "route_distance_km": None,
            "road_distance_km": None, "duration_min": None,
            "status": "routing_unconfigured", "routing_engine": None,
            "note": "No road-routing provider configured",
        }
        with patch("tourist.management.commands.audit_routing.provider_config",
                   return_value={"enabled": False, "base_url": "",
                                 "api_key": "", "source": "environment"}):
            with patch("tourist.management.commands.audit_routing.route_metrics",
                       return_value=payload):
                output = self._run()
        self.assertIn("NOT VERIFIED", output)
        self.assertIn("provider enabled : False", output)
        self.assertIn("base URL set    : False", output)

    def test_reports_verified_when_provider_is_healthy(self):
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(225.0, 300)):
            with patch("tourist.management.commands.audit_routing.provider_config",
                       return_value={"enabled": True, "base_url": "http://routing:5000",
                                     "api_key": "", "source": "environment"}):
                output = self._run()
        self.assertIn("VERIFIED", output)
        self.assertNotIn("NOT VERIFIED", output)
        self.assertIn("real-road", output)

    def test_flags_an_impossible_route(self):
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(50.0)):
            with patch("tourist.management.commands.audit_routing.provider_config",
                       return_value={"enabled": True, "base_url": "http://routing:5000",
                                     "api_key": "", "source": "environment"}):
                output = self._run()
        self.assertIn("NOT VERIFIED", output)
        self.assertIn("shorter than", output)

    def test_json_output_is_parseable_and_honest(self):
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(225.0, 300)):
            with patch("tourist.management.commands.audit_routing.provider_config",
                       return_value={"enabled": True, "base_url": "http://routing:5000",
                                     "api_key": "", "source": "environment"}):
                payload = json.loads(self._run(json=True))
        self.assertTrue(payload["road_verified"])
        self.assertTrue(payload["base_url_configured"])
        self.assertTrue(payload["probes"])
        for probe in payload["probes"]:
            self.assertIn("is_road_verified", probe)
            self.assertIn("detour_ratio", probe)

    def test_missing_probe_pair_is_reported_not_silently_skipped(self):
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(225.0, 300)):
            with patch("tourist.management.commands.audit_routing.provider_config",
                       return_value={"enabled": True, "base_url": "http://routing:5000",
                                     "api_key": "", "source": "environment"}):
                output = self._run()
        # The second pair has no matching destinations in the fixture and must
        # say so rather than disappear.
        self.assertIn("pokhara-beni", output)
        self.assertIn("not found", output)

    def test_audit_changes_nothing(self):
        before = list(Destination.objects.values_list("id", "latitude", "longitude"))
        with patch("tourist.management.commands.audit_routing.route_metrics",
                   return_value=route_payload(225.0, 300)):
            self._run()
        after = list(Destination.objects.values_list("id", "latitude", "longitude"))
        self.assertEqual(before, after)
