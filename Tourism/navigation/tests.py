"""Navigation subsystem tests: provider abstraction, map matching,
progress/off-route detection, fallback honesty and rate limiting."""
from __future__ import annotations

import json
from pathlib import Path

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
        self.assertIn(src, ("graphml_fallback", "straight_line_fallback"))
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
        self.assertEqual(r["source"], "straight_line_fallback")
        straight = haversine_m(28.2096, 83.9856, 28.1929, 83.9810)
        self.assertGreater(r["distance_m"], straight)  # detour factor applied
        self.assertIn("NOT a road route", r["note"])


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=0, ROUTING_CACHE_TTL=0)
class DiagnosticsTests(APITestCase):
    """Every road-route request is recorded; admins can see fallback rate."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_route_request_records_diagnostics_and_admin_can_read(self):
        from django.contrib.auth import get_user_model
        from navigation.models import RouteDiagnostics
        r = self.client.post("/api/v1/navigation/road-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "destination": {"latitude": 28.1929, "longitude": 83.9810},
            "mode": "driving"}, format="json")
        self.assertEqual(r.status_code, 200)
        row = RouteDiagnostics.objects.latest("created_at")
        self.assertTrue(row.fallback)  # no OSRM configured here
        self.assertIn(row.provider, ("graphml_fallback", "straight_line_fallback"))
        self.assertGreater(row.distance_m, 0)
        # anonymous cannot read diagnostics
        self.assertIn(self.client.get("/api/v1/navigation/diagnostics/").status_code, (401, 403))
        admin = get_user_model().objects.create_superuser(
            email="nav-admin@example.com", password="AdminPass123!")
        self.client.force_authenticate(user=admin)
        resp = self.client.get("/api/v1/navigation/diagnostics/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_requests"], 1)
        self.assertEqual(resp.data["fallback_count"], 1)
        self.assertEqual(resp.data["fallback_rate"], 1.0)


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=0, ROUTING_CACHE_TTL=0)
class MultiStopAndContextTests(APITestCase):
    """Multi-stop routing, alternative selection, along-route nearby,
    and context layers (safety/weather) — all against the labelled
    fallback chain here; identical code paths serve real OSRM."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        from tourist.models import Destination
        self.dest = Destination.objects.create(
            name="Context Falls", slug="context-falls", district="Kaski",
            description="d", latitude=28.1900, longitude=83.9800,
            status="approved", is_active=True)

    def _route(self):
        r = self.client.post("/api/v1/navigation/road-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "destination": {"latitude": 28.1929, "longitude": 83.9810},
            "mode": "driving"}, format="json")
        self.assertEqual(r.status_code, 200)
        return r.data

    def test_itinerary_route_legs_and_totals(self):
        r = self.client.post("/api/v1/navigation/itinerary-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "stops": [
                {"id": 7, "name": "Davis Falls", "latitude": 28.1834, "longitude": 83.9762},
                {"id": 9, "name": "Peace Pagoda", "latitude": 28.1951, "longitude": 83.9742},
            ],
            "mode": "driving"}, format="json")
        self.assertEqual(r.status_code, 200)
        data = r.data
        self.assertEqual(data["totals"]["legs"], 2)
        self.assertEqual(len(data["legs"]), 2)
        self.assertEqual(data["legs"][0]["to"]["name"], "Davis Falls")
        self.assertEqual(data["legs"][0]["to"]["stop_id"], 7)
        for leg in data["legs"]:
            self.assertTrue(leg["route_id"])
            self.assertGreaterEqual(leg["distance_m"], 0)
            self.assertGreater(len(leg["geometry"]), 1)
        self.assertAlmostEqual(
            data["totals"]["distance_m"],
            sum(l["distance_m"] for l in data["legs"]), places=1)
        # each leg is independently navigable
        p = self.client.post("/api/v1/navigation/progress/", {
            "route_id": data["legs"][0]["route_id"],
            "latitude": 28.2096, "longitude": 83.9856, "accuracy": 10}, format="json")
        self.assertEqual(p.status_code, 200)

    def test_itinerary_diagnostics_recorded(self):
        from navigation.models import RouteDiagnostics
        self.client.post("/api/v1/navigation/itinerary-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "stops": [{"latitude": 28.1834, "longitude": 83.9762}],
            "mode": "driving"}, format="json")
        row = RouteDiagnostics.objects.filter(provider__startswith="itinerary:").first()
        self.assertIsNotNone(row)
        self.assertTrue(row.fallback)

    def test_select_alternative_without_alternatives_404(self):
        data = self._route()
        r = self.client.post("/api/v1/navigation/select-alternative/", {
            "route_id": data["route"]["route_id"], "index": 0}, format="json")
        # fallback providers expose no alternatives -> honest 404, not a fake swap
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.data["error"], "no_such_alternative")

    def test_along_route_sorts_by_route_distance(self):
        from tourist.models import Hospital
        Hospital.objects.create(name="Corridor Hospital", latitude=28.2000,
                                longitude=83.9825, destination=self.dest)
        Hospital.objects.create(name="Far Hospital", latitude=27.9000,
                                longitude=84.4000, destination=self.dest)
        data = self._route()
        r = self.client.get(
            f"/api/v1/navigation/along-route/?route_id={data['route']['route_id']}"
            "&category=hospital&radius_m=3000")
        self.assertEqual(r.status_code, 200)
        names = [i["name"] for i in r.data["items"]]
        self.assertIn("Corridor Hospital", names)
        self.assertNotIn("Far Hospital", names)
        first = r.data["items"][0]
        self.assertGreaterEqual(first["along_route_m"], 0)

    def test_route_context_layers_are_labelled_and_route_untouched(self):
        from tourist.models import CurrentHazard
        from django.utils import timezone
        CurrentHazard.objects.create(
            destination=self.dest, hazard_type="landslide", title="Trial road landslide",
            severity="moderate", source_type="official", source_name="DoR",
            observed_at=timezone.now())
        data = self._route()
        r = self.client.get(
            f"/api/v1/navigation/route-context/?route_id={data['route']['route_id']}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("never alter the route", r.data["safety"]["note"])
        self.assertTrue(r.data["weather"]["note"])
        titles = [w["title"] for w in r.data["safety"]["warnings"]]
        self.assertIn("Trial road landslide", titles)
        # route itself unchanged
        again = self.client.get(
            f"/api/v1/navigation/along-route/?route_id={data['route']['route_id']}"
            "&category=hospital")
        self.assertEqual(again.status_code, 200)

    def test_itinerary_validation_bounds(self):
        r = self.client.post("/api/v1/navigation/itinerary-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "stops": [], "mode": "driving"}, format="json")
        self.assertEqual(r.status_code, 400)


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=0, ROUTING_CACHE_TTL=0,
                   NAVIGATION_ALLOW_DEBUG=True)
class GPSReplayFixtureTests(APITestCase):
    """Deterministic GPS fixtures through the replay endpoint: the CI-run
    equivalent of driving around Pokhara (normal, jitter, poor accuracy,
    wrong turn, tunnel loss, arrival)."""

    FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gps"

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        # Synthetic session with the exact corridor the fixtures follow —
        # deterministic and provider-independent (state-machine testing).
        from navigation.navigation_service import create_session
        self.route_id = create_session({
            "source": "fixture", "mode": "driving",
            "distance_m": 2000.0, "duration_s": 400.0,
            "geometry": [[28.2096, 83.9856], [28.2050, 83.9830],
                         [28.1929, 83.9810]],
            "bounds": None,
            "steps": [
                {"instruction": "Head south", "distance_m": 800.0,
                 "duration_s": 160.0, "maneuver": "depart"},
                {"instruction": "Turn right", "distance_m": 1200.0,
                 "duration_s": 240.0, "maneuver": "turn-right"},
            ],
        })

    def _replay(self, name):
        fx = json.loads((self.FIXTURE_DIR / f"{name}.json").read_text())
        resp = self.client.post("/api/v1/navigation/debug/replay/", {
            "route_id": self.route_id, "fixes": fx["fixes"]}, format="json")
        self.assertEqual(resp.status_code, 200)
        return fx["expect"], resp.data["results"]

    def test_all_fixtures(self):
        for name in ("normal_drive", "gps_jitter", "poor_accuracy",
                     "wrong_turn", "tunnel_loss", "arrival"):
            expect, results = self._replay(name)
            off = sum(1 for r in results if not r["on_route"])
            reroute = any(r["reroute_required"] for r in results)
            if "final_arrived" in expect:
                self.assertEqual(results[-1]["arrived"], expect["final_arrived"],
                                 f"{name}: arrival expectation")
            if "off_route_max" in expect:
                self.assertLessEqual(off, expect["off_route_max"],
                                     f"{name}: {off} off-route fixes")
            if "off_route_min" in expect:
                self.assertGreaterEqual(off, expect["off_route_min"],
                                        f"{name}: expected deviation")
            if expect.get("reroute_seen"):
                self.assertTrue(reroute, f"{name}: reroute expected")

    def test_replay_disabled_by_default(self):
        from django.test import override_settings as ov
        with ov(NAVIGATION_ALLOW_DEBUG=False):
            resp = self.client.post("/api/v1/navigation/debug/replay/", {
                "route_id": self.route_id, "fixes": []}, format="json")
        self.assertEqual(resp.status_code, 403)


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=0, ROUTING_CACHE_TTL=0)
class SessionLifecycleTests(APITestCase):
    """Server-side session tracking + resume + end."""

    def _route(self):
        r = self.client.post("/api/v1/navigation/road-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "destination": {"latitude": 28.1929, "longitude": 83.9810},
            "mode": "driving"}, format="json")
        return r.data

    def test_progress_tracks_session_and_end_closes_it(self):
        from navigation.models import NavigationSession
        data = self._route()
        rid = data["route"]["route_id"]
        geo = data["route"]["geometry"]
        # an actual vertex of the returned polyline — on-route for any
        # geometry (straight-line fallback or corridor graph alike)
        mid = geo[len(geo) // 2]
        self.client.post("/api/v1/navigation/progress/", {
            "route_id": rid, "latitude": mid[0], "longitude": mid[1],
            "accuracy": 8}, format="json")
        sess = NavigationSession.objects.get(session_id=rid)
        self.assertEqual(sess.status, "NAVIGATING")
        self.assertEqual(sess.fix_count, 1)
        self.assertGreater(sess.progress, 0)
        # active session discoverable for resume
        act = self.client.get("/api/v1/navigation/sessions/active/")
        self.assertEqual(act.data["session"]["session_id"], rid)
        # off-route fix increments counter
        self.client.post("/api/v1/navigation/progress/", {
            "route_id": rid, "latitude": 28.2050, "longitude": 83.9950,
            "accuracy": 6}, format="json")
        sess.refresh_from_db()
        self.assertEqual(sess.status, "OFF_ROUTE")
        self.assertEqual(sess.off_route_count, 1)
        # end closes it; no longer offered for resume
        e = self.client.post("/api/v1/navigation/end/", {"route_id": rid}, format="json")
        self.assertTrue(e.data["ended"])
        act = self.client.get("/api/v1/navigation/sessions/active/")
        self.assertIsNone(act.data["session"])


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=0, ROUTING_CACHE_TTL=0)
class HealthAndPolicyTests(APITestCase):
    def test_health_reports_unconfigured_honestly(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_superuser(
            email="nav-health@example.com", password="AdminPass123!")
        self.client.force_authenticate(user=admin)
        r = self.client.get("/api/v1/navigation/health/?fresh=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "unconfigured")  # no ROUTING_BASE_URL
        self.assertFalse(r.data["profiles"]["walking"] == "available")

    def test_fallback_route_flagged_not_navigation_grade(self):
        r = self.client.post("/api/v1/navigation/road-route/", {
            "start": {"latitude": 28.2096, "longitude": 83.9856},
            "destination": {"latitude": 28.1929, "longitude": 83.9810},
            "mode": "driving"}, format="json")
        self.assertFalse(r.data["route"]["navigation_grade"])
        self.assertIn(r.data["route"]["source"],
                      ("graphml_fallback", "straight_line_fallback"))


@override_settings(ROUTING_BASE_URL="", ROUTING_RATE_LIMIT=0, ROUTING_CACHE_TTL=0)
class LegacyRouteContractTests(APITestCase):
    """§17: the legacy POST /navigation/route contract keeps working, but
    ground modes now ride the real road-routing provider chain (labelled)."""

    def test_legacy_body_returns_road_provider_fields(self):
        r = self.client.post("/api/v1/navigation/route", {
            "start_latitude": 28.2096, "start_longitude": 83.9856,
            "end_latitude": 28.1929, "end_longitude": 83.9810,
            "transport_mode": "Private Car / Taxi"}, format="json")
        self.assertEqual(r.status_code, 200)
        data = r.data
        # legacy keys preserved
        self.assertGreater(data["distance_km"], 0)
        self.assertTrue(data["route"])
        self.assertIn("lat", data["route"][0])
        # new road-routing fields present and honest
        self.assertIn(data["source"],
                      ("osrm", "graphml_fallback", "straight_line_fallback"))
        self.assertIsInstance(data["navigation_grade"], bool)
        self.assertEqual(data["navigation_grade"], data["source"] == "osrm")
        self.assertTrue(data["routing_engine"].startswith("road_provider:"))

    def test_flight_never_road_routed(self):
        r = self.client.post("/api/v1/navigation/route", {
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "end_latitude": 28.2096, "end_longitude": 83.9856,
            "transport_mode": "flight"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data["duration_min"])  # no invented flight times
        self.assertNotIn("navigation_grade", r.data)


class TurnByTurnStepsTests(TestCase):
    """Maneuvers must come from real geometry; fallbacks must stay honest."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_build_maneuvers_detects_turns_from_geometry(self):
        from navigation.route_engine import build_maneuvers
        # L-shaped: head east, then a 90° right turn to head south
        route = {"source": "graphml_fallback", "distance_m": 2000.0,
                 "geometry": [[28.0, 84.0], [28.0, 84.01], [27.99, 84.01]]}
        steps = build_maneuvers(route)
        self.assertGreaterEqual(len(steps), 3)
        self.assertTrue(steps[0]["instruction"].startswith("Head "))
        self.assertIn("right", steps[1]["instruction"])
        self.assertEqual(steps[-1]["instruction"], "Arrive at destination")
        self.assertEqual(steps[0]["maneuver_grade"], "corridor-node")
        self.assertGreater(steps[0]["distance_m"], 0)

    def test_build_maneuvers_straight_line_is_honest(self):
        from navigation.route_engine import build_maneuvers
        steps = build_maneuvers({"source": "straight_line_fallback",
                                 "distance_m": 5000.0,
                                 "geometry": [[28.0, 84.0], [28.04, 84.0]]})
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["maneuver_grade"], "none")
        self.assertIn("Straight-line", steps[0]["instruction"])

    def test_cached_route_backfills_steps_when_provider_omits_them(self):
        from unittest import mock
        from navigation import route_engine

        class NoStepProvider:
            name = "nostep"
            supported_modes = ("driving",)

            def supports(self, mode):
                return True

            def route(self, start, destination, mode):
                return {"source": "graphml_fallback", "mode": mode,
                        "distance_m": 1000.0, "duration_s": 100.0,
                        "geometry": [[28.0, 84.0], [28.0, 84.005], [27.995, 84.005]]}

        with mock.patch.object(route_engine, "provider_chain",
                               return_value=[NoStepProvider()]):
            result, _ = route_engine.cached_route((28.0, 84.0), (27.995, 84.005),
                                                  "driving", use_cache=False)
        steps = result["route"]["steps"]
        self.assertGreaterEqual(len(steps), 3)
        self.assertTrue(all(s["instruction"] for s in steps))


class CalculateStepsAPITests(APITestCase):
    """The public calculate endpoint must expose real turn-by-turn steps."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_calculate_returns_steps(self):
        r = self.client.post("/api/v1/navigation/calculate/", {
            "origin_lat": 27.7172, "origin_lng": 85.3240,
            "destination_name": "Pokhara",
            "transport_mode": "Private Car / Taxi",
        }, format="json")
        self.assertEqual(r.status_code, 200)
        steps = r.data.get("steps") or []
        self.assertTrue(steps, "calculate must return turn-by-turn steps")
        self.assertTrue(all(s.get("instruction") for s in steps))
        grades = {s.get("maneuver_grade", "") for s in steps}
        self.assertIn(r.data.get("route_source"),
                      ("osrm", "graphml_fallback", "straight_line_fallback"))
        self.assertTrue(grades)
