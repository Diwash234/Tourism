"""Navigation must give real street-level turn-by-turn steps when a routing
engine is reachable, and stay honest (labelled approximation) when not."""
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

OSRM_PAYLOAD = {
    "code": "Ok",
    "routes": [{
        "distance": 5130.0, "duration": 540.0,
        "geometry": {"coordinates": [[83.9855, 28.2096], [83.9870, 28.2110], [83.9890, 28.2125], [83.9921, 28.2150]]},
        "legs": [{"steps": [
            {"distance": 900.0, "duration": 100.0, "name": "Lakeside Road",
             "maneuver": {"type": "depart", "location": [83.9855, 28.2096]}},
            {"distance": 2300.0, "duration": 240.0, "name": "Sarangkot Road",
             "maneuver": {"type": "turn", "modifier": "left", "location": [83.9870, 28.2110]}},
            {"distance": 1930.0, "duration": 200.0, "name": "",
             "maneuver": {"type": "turn", "modifier": "slight right", "location": [83.9890, 28.2125]}},
            {"distance": 0.0, "duration": 0.0, "name": "",
             "maneuver": {"type": "arrive", "location": [83.9921, 28.2150]}},
        ]}],
    }],
}


class _Resp:
    status_code = 200

    def json(self):
        return OSRM_PAYLOAD

    def raise_for_status(self):
        return None


def fake_get(url, *args, **kwargs):
    """OSRM answers; every other outbound call behaves as if offline."""
    import requests
    if "/route/v1/" in url:
        return _Resp()
    raise requests.ConnectionError("offline in tests")


@override_settings(ROUTING_BASE_URL="http://osrm.test", ROUTING_PROFILES=["driving"], ROUTING_RATE_LIMIT=0)
class StreetLevelTurnByTurnTests(TestCase):
    def setUp(self):
        cache.clear()
        self.body = {"start_latitude": 28.2096, "start_longitude": 83.9855,
                     "end_latitude": 28.2150, "end_longitude": 83.9921,
                     "transport_mode": "Private Car / Taxi"}

    def test_route_page_endpoint_returns_named_turn_steps(self):
        with mock.patch("requests.get", side_effect=fake_get):
            res = self.client.post("/api/v1/navigation/route", self.body, content_type="application/json")
        self.assertEqual(res.status_code, 200, res.content)
        data = res.json()
        self.assertEqual(data["source"], "osrm")
        self.assertTrue(data["navigation_grade"])
        self.assertEqual(data["distance_km"], 5.13)
        steps = data["steps"]
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[1]["turn"], "left")
        self.assertIn("Sarangkot Road", steps[1]["instruction"])
        self.assertEqual(steps[2]["turn"], "slight_right")
        self.assertEqual(steps[1]["distance_km"], 2.3)
        self.assertEqual(steps[1]["location"], [28.2110, 83.9870])
        self.assertEqual(steps[1]["name"], "Sarangkot Road")
        self.assertGreater(len(data["route"]), 3)

    def test_live_navigation_route_is_navigation_grade(self):
        body = {"start": {"latitude": 28.2096, "longitude": 83.9855},
                "destination": {"latitude": 28.2150, "longitude": 83.9921}, "mode": "driving"}
        with mock.patch("requests.get", side_effect=fake_get):
            res = self.client.post("/api/v1/navigation/road-route/", body, content_type="application/json")
        self.assertEqual(res.status_code, 200, res.content)
        route = res.json()["route"]
        self.assertTrue(route["navigation_grade"])
        self.assertEqual(route["source"], "osrm")
        self.assertIn("Sarangkot Road", res.json()["steps"][1]["instruction"])

    def test_walking_mode_is_left_on_the_existing_path(self):
        from tourist.views_compat import _street_level_route
        self.assertIsNone(_street_level_route(28.2, 83.98, 28.21, 83.99, "walking / trek"))


@override_settings(ROUTING_BASE_URL="")
class NoEngineStaysHonestTests(TestCase):
    def test_without_an_engine_the_route_is_labelled_not_navigation_grade(self):
        cache.clear()
        res = self.client.post("/api/v1/navigation/route", {
            "start_latitude": 28.2096, "start_longitude": 83.9855,
            "end_latitude": 28.2150, "end_longitude": 83.9921,
            "transport_mode": "Private Car / Taxi"}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json().get("navigation_grade"))
