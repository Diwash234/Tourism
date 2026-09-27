"""Tests for the live weather provider.

Every test mocks the network: the suite must not depend on an external service
being up. The point of these tests is the contract, not the forecast.
"""
from __future__ import annotations

from unittest.mock import patch

import requests
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from tourist.weather_service import (
    DEFAULT_PROVIDER_URL,
    WMO_CODES,
    describe_weather_code,
    fetch_weather,
    provider_config,
)

KATHMANDU = (27.7172, 85.3240)

GOOD_PAYLOAD = {
    "latitude": 27.73,
    "longitude": 85.34,
    "elevation": 1301.0,
    "timezone": "Asia/Kathmandu",
    "current": {
        "time": "2026-09-27T11:45",
        "temperature_2m": 22.8,
        "apparent_temperature": 25.2,
        "relative_humidity_2m": 76,
        "precipitation": 0.4,
        "weather_code": 80,
        "cloud_cover": 90,
        "wind_speed_10m": 5.0,
        "wind_gusts_10m": 28.8,
        "wind_direction_10m": 139,
        "is_day": 1,
    },
    "daily": {
        "time": ["2026-09-27", "2026-09-28"],
        "weather_code": [80, 55],
        "temperature_2m_max": [23.2, 26.8],
        "temperature_2m_min": [17.5, 15.8],
        "precipitation_sum": [17.7, 2.6],
        "precipitation_probability_max": [100, 100],
        "uv_index_max": [2.25, 7.75],
        "sunrise": ["2026-09-27T05:54", "2026-09-28T05:55"],
        "sunset": ["2026-09-27T18:04", "2026-09-28T18:02"],
        "wind_speed_10m_max": [12.0, 9.0],
    },
}


def fake_response(payload=None, status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response._content = (payload if payload is not None else GOOD_PAYLOAD)
    if isinstance(response._content, dict):
        import json

        response._content = json.dumps(response._content).encode("utf-8")
    response.headers["Content-Type"] = "application/json"
    response.url = DEFAULT_PROVIDER_URL
    return response


class WmoCodeTests(TestCase):
    def test_known_codes_describe_themselves(self):
        self.assertEqual(describe_weather_code(0), "Clear sky")
        self.assertEqual(describe_weather_code(95), "Thunderstorm")
        self.assertEqual(describe_weather_code(99), "Thunderstorm with heavy hail")

    def test_unknown_or_malformed_code_is_none_not_a_guess(self):
        self.assertIsNone(describe_weather_code(1234))
        self.assertIsNone(describe_weather_code("abc"))
        self.assertIsNone(describe_weather_code(None))

    def test_code_table_is_the_published_wmo_set(self):
        # A spot check that we did not invent a table.
        for code in (0, 45, 65, 75, 95, 99):
            self.assertIn(code, WMO_CODES)


class ProviderConfigTests(TestCase):
    def test_default_is_the_keyless_open_meteo_endpoint(self):
        config = provider_config()
        self.assertTrue(config["enabled"])
        self.assertEqual(config["base_url"], DEFAULT_PROVIDER_URL)
        self.assertTrue(DEFAULT_PROVIDER_URL.startswith("https://"))

    def test_plain_http_provider_is_refused(self):
        """The HTTPS guard lives in provider_config, so test it there for real."""
        from tourist.models import SiteSetting

        SiteSetting.objects.create(
            key="weather_provider",
            value={"enabled": True, "base_url": "http://insecure.example/v1", "api_key": ""},
            description="test",
        )
        config = provider_config()
        self.assertFalse(config["enabled"])
        self.assertEqual(config["reason"], "provider_url_must_be_https")

        with patch("tourist.weather_service.requests.get") as mocked:
            result = fetch_weather(*KATHMANDU, use_cache=False)
        mocked.assert_not_called()
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "provider_url_must_be_https")

    def test_admin_can_disable_the_provider_entirely(self):
        from tourist.models import SiteSetting

        SiteSetting.objects.create(
            key="weather_provider",
            value={"enabled": False, "base_url": DEFAULT_PROVIDER_URL, "api_key": ""},
            description="test",
        )
        with patch("tourist.weather_service.requests.get") as mocked:
            result = fetch_weather(*KATHMANDU, use_cache=False)
        mocked.assert_not_called()
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "disabled_by_admin")


class WeatherFetchTests(TestCase):
    def test_live_payload_is_parsed_into_current_and_daily(self):
        with patch("tourist.weather_service.requests.get", return_value=fake_response()):
            result = fetch_weather(*KATHMANDU, forecast_days=2, use_cache=False)
        self.assertTrue(result.available)
        self.assertEqual(result.current["temperature_c"], 22.8)
        self.assertEqual(result.current["description"], "Slight rain showers")
        self.assertEqual(result.current["kind"], "model_forecast")
        self.assertEqual(len(result.daily), 2)
        self.assertEqual(result.daily[1]["description"], "Dense drizzle")
        self.assertEqual(result.daily[0]["precipitation_sum_mm"], 17.7)
        self.assertEqual(result.coordinates["timezone"], "Asia/Kathmandu")

    def test_null_island_never_reaches_the_provider(self):
        with patch("tourist.weather_service.requests.get") as mocked:
            result = fetch_weather(0, 0, use_cache=False)
        mocked.assert_not_called()
        self.assertFalse(result.available)
        self.assertIn("null_island", result.reason)

    def test_timeout_degrades_with_a_reason_and_no_reading(self):
        with patch("tourist.weather_service.requests.get", side_effect=requests.Timeout()):
            result = fetch_weather(*KATHMANDU, use_cache=False)
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "provider_timeout")
        self.assertEqual(result.current, {})
        self.assertEqual(result.daily, [])

    def test_connection_error_degrades(self):
        with patch(
            "tourist.weather_service.requests.get",
            side_effect=requests.ConnectionError("dns"),
        ):
            result = fetch_weather(*KATHMANDU, use_cache=False)
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "provider_unavailable")

    def test_unexpected_exception_never_escapes_as_a_500(self):
        with patch("tourist.weather_service.requests.get", side_effect=OSError("boom")):
            result = fetch_weather(*KATHMANDU, use_cache=False)
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "provider_error")

    def test_http_error_status_degrades(self):
        with patch("tourist.weather_service.requests.get", return_value=fake_response(status_code=503)):
            result = fetch_weather(*KATHMANDU, use_cache=False)
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "provider_unavailable")

    def test_empty_current_block_degrades(self):
        payload = dict(GOOD_PAYLOAD)
        payload["current"] = {}
        with patch("tourist.weather_service.requests.get", return_value=fake_response(payload)):
            result = fetch_weather(*KATHMANDU, use_cache=False)
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "no_current_conditions")

    def test_result_is_cached(self):
        from django.core.cache import cache

        cache.clear()
        with patch("tourist.weather_service.requests.get", return_value=fake_response()) as mocked:
            first = fetch_weather(*KATHMANDU, use_cache=True)
            second = fetch_weather(*KATHMANDU, use_cache=True)
        self.assertTrue(first.available and second.available)
        self.assertEqual(mocked.call_count, 1, "second read should come from cache")


class WeatherApiTests(APITestCase):
    def test_endpoint_returns_real_data(self):
        with patch("tourist.weather_service.requests.get", return_value=fake_response()):
            response = self.client.get("/api/v1/weather/?lat=27.7172&lon=85.3240&days=2")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["available"])
        self.assertEqual(payload["current"]["temperature_c"], 22.8)
        self.assertEqual(payload["coordinates_source"], "requested")

    def test_endpoint_returns_200_when_the_provider_is_down(self):
        with patch("tourist.weather_service.requests.get", side_effect=requests.Timeout()):
            response = self.client.get("/api/v1/weather/?lat=27.7172&lon=85.3240")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["available"])
        self.assertEqual(payload["reason"], "provider_timeout")

    def test_endpoint_rejects_null_island(self):
        response = self.client.get("/api/v1/weather/?lat=0&lon=0")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["available"])
        self.assertIn("null_island", response.json()["reason"])

    def test_endpoint_without_coordinates_is_a_clear_400(self):
        response = self.client.get("/api/v1/weather/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["reason"], "no_coordinates")

    def test_provider_status_never_leaks_the_key(self):
        response = self.client.get("/api/v1/weather/provider")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("api_key", response.json())
        self.assertTrue(response.json()["configured"])
