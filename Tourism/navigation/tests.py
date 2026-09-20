"""Navigation subsystem tests: provider abstraction, map matching,
progress/off-route detection, fallback honesty and rate limiting."""
from __future__ import annotations

from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from navigation.fallback_providers import StraightLineProvider
from navigation.map_matching import (haversine_m, match_point_to_route,
                                     off_route_threshold_m)
from navigation.navigation_service import compute_progress, create_session
from navigation.osrm_provider import OSRMProvider

# A short Pokhara-ish route: Lakeside -> Davis Falls direction (3 points)
GEOMETRY = [[28.2096, 83.9856], [28.2050, 83.9830], [28.1929, 83.9810]]


def osrm_payload():
    return {
        "code": "Ok",
        "routes": [{
            "distance": 2800.0,
            "duration": 480.0,
            "geometry": {"type": "LineString", "coordinates": [
                [83.9856, 28.2096], [83.9830, 28.2050], [83.9810, 28.1929]]},
            "legs": [{"steps": [
                {"distance": 350.0, "duration": 60.0, "name": "Lakeside Road",
                 "maneuver": {"type": "depart", "modifier": "south"}},
                {"distance": 600.0, "duration": 90.0, "name": "Harbor Road",
                 "maneuver": {"type": "turn", "modifier": "right"}},
                {"distance": 1850.0, "duration": 330.0, "name": "",
                 "maneuver": {"type": "arrive"}},
            ]}],
        }, {
            "distance": 3100.0, "duration": 540.0,
            "geometry": {"type": "LineString", "coordinates": [
                [83.9856, 28.2096], [83.9810, 28.1929]]},
            "legs": [{"steps": []}],
        }],
    }


class MapMatchingTests(TestCase):
    def test_haversine_known_distance(self):
        # ~1.85 km between the first and last geometry points
        d = haversine_m(28.2096, 83.9856, 28.1929, 83.9810)
        self.assertGreater(d, 1700)
        self.assertLess(d, 2000)

    def test_point_on_route_snaps_close(self):
        m = match_point_to_route((28.2050, 83.9830), GEOMETRY)
        self.assertLess(m["distance_from_route_m"], 1.0)
        self.assertGreater(m["traveled_m"], 0)

    def test_point_off_route_reports_distance(self):
        # ~700 m east of the middle vertex
        m = match_point_to_route((28.2050, 83.9900), GEOMETRY)
        self.assertGreater(m["distance_from_route_m"], 400)

    def test_plan_threshold_examples(self):
        # accuracy 7 m, 12 m from route -> ON route
        self.assertGreater(off_route_threshold_m(7), 12)
        # accuracy 8 m, 75 m from route -> OFF route
        self.assertLess(off_route_threshold_m(8), 75)


@override_settings(ROUTING_BASE_URL="https://osrm.example.org",
                   ROUTING_PROFILES=["driving", "foot", "bike"])
class OSRMProviderTests(TestCase):
    @mock.patch("navigation.osrm_provider.requests.get")
    def test_parses_canonical_route(self, get):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = osrm_payload()
        get.return_value = resp
        p = OSRMProvider()
        route = p.route((28.2096, 83.9856), (28.1929, 83.9810), "driving")
        self.assertEqual(route["source"], "osrm")
        self.assertEqual(route["distance_m"], 2800.0)
        self.assertEqual(len(route["geometry"]), 3)
        self.assertEqual(route["geometry"][0], [28.2096, 83.9856])
        self.assertEqual(route["steps"][0]["instruction"], "Head out onto Lakeside Road")
        self.assertEqual(route["steps"][1]["instruction"], "Turn right onto Harbor Road")
        self.assertEqual(route["steps"][2]["maneuver"], "arrive")

    @mock.patch("navigation.osrm_provider.requests.get")
    def test_alternatives_skip_primary(self, get):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = osrm_payload()
        get.return_value = resp
        p = OSRMProvider()
        alts = p.alternatives((28.2096, 83.9856), (28.1929, 83.9810), "driving")
        self.assertEqual(len(alts), 1)
        self.assertEqual(alts[0]["distance_m"], 3100.0)

    def test_unhosted_profile_not_pretended(self):
        p = OSRMProvider(base_url="https://osrm.example.org",
                         available_profiles=("driving",))
        self.assertFalse(p.supports("walking"))
        self.assertIsNone(p.route((28.2, 83.9), (28.1, 83.9), "walking"))


class ProgressServiceTests(TestCase):
    def _route(self):
        return {
            "source": "test", "mode": "driving", "distance_m": 2000.0,
            "duration_s": 400.0, "geometry": GEOMETRY, "bounds": None,
            "steps": [
                {"instruction": "Head south onto Lakeside Road", "distance_m": 800.0,
                 "duration_s": 160.0, "maneuver": "depart"},
                {"instruction": "Turn right onto Harbor Road", "distance_m": 1200.0,
                 "duration_s": 240.0, "maneuver": "turn-right"},
            ],
        }

    def test_create_and_compute_on_route(self):
        rid = create_session(self._route())
        from navigation.navigation_service import get_session
        route = get_session(rid)
        p = compute_progress(route, 28.2050, 83.9830, accuracy=8)
        self.assertTrue(p["on_route"])
        self.assertFalse(p["reroute_required"])
        self.assertGreater(p["distance_remaining_m"], 0)
        self.assertLess(p["distance_remaining_m"], 2000.0)
        self.assertEqual(p["next_instruction"]["instruction"],
                         "Turn right onto Harbor Road")
        self.assertGreater(p["progress"], 0.1)

    def test_off_route_triggers_reroute(self):
        route = self._route()
        create_session(route)  # populates helper fields on the dict
        p = compute_progress(route, 28.2050, 83.9900, accuracy=8)
        self.assertFalse(p["on_route"])
        self.assertTrue(p["reroute_required"])

    def test_arrival_detected(self):
        route = self._route()
        create_session(route)
        p = compute_progress(route, 28.1929, 83.9810, accuracy=5)
        self.assertTrue(p["arrived"])


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=3, ROUTING_CACHE_TTL=0)
class NavigationEndpointTests(APITestCase):
    BODY = {"start": {"latitude": 28.2096, "longitude": 83.9856},
            "destination": {"latitude": 28.1929, "longitude": 83.9810},
            "mode": "driving"}

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_fallback_route_is_honest_and_progress_works(self):
        r = self.client.post("/api/v1/navigation/road-route/", self.BODY, format="json")
        self.assertEqual(r.status_code, 200)
        data = r.data
        self.assertEqual(data["status"], "success")
        src = data["route"]["source"]
        self.assertIn(src, ("bundled_graph_estimate", "straight_line_estimate"))
        self.assertTrue(data["route"]["note"])  # honest caveat present
        self.assertTrue(data["steps"])
        rid = data["route"]["route_id"]
        geo = data["route"]["geometry"]
        mid = geo[len(geo) // 2]
        p = self.client.post("/api/v1/navigation/progress/", {
            "route_id": rid, "latitude": mid[0], "longitude": mid[1],
            "heading": 172, "accuracy": 8}, format="json")
        self.assertEqual(p.status_code, 200)
        self.assertTrue(p.data["on_route"])
        self.assertFalse(p.data["reroute_required"])

    def test_unknown_route_id_404(self):
        p = self.client.post("/api/v1/navigation/progress/", {
            "route_id": "nope", "latitude": 28.2, "longitude": 83.9}, format="json")
        self.assertEqual(p.status_code, 404)

    def test_invalid_mode_400(self):
        body = {**self.BODY, "mode": "helicopter"}
        r = self.client.post("/api/v1/navigation/road-route/", body, format="json")
        self.assertEqual(r.status_code, 400)

    def test_modes_endpoint_lists_supported_only(self):
        r = self.client.get("/api/v1/navigation/modes/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("driving", r.data["modes"])
        self.assertFalse(r.data["configured"])  # no ROUTING_BASE_URL here

    def test_rate_limit_429(self):
        codes = [self.client.post("/api/v1/navigation/road-route/",
                                  self.BODY, format="json").status_code
                 for _ in range(5)]
        self.assertIn(429, codes)
        self.assertEqual(codes[0], 200)


class StraightLineHonestyTests(TestCase):
    def test_estimate_labelled_and_detoured(self):
        r = StraightLineProvider().route((28.2096, 83.9856), (28.1929, 83.9810), "driving")
        self.assertEqual(r["source"], "straight_line_estimate")
        straight = haversine_m(28.2096, 83.9856, 28.1929, 83.9810)
        self.assertGreater(r["distance_m"], straight)  # detour factor applied
        self.assertIn("NOT a road route", r["note"])
