"""Live weather with an admin-configurable provider and honest degradation.

Default provider: Open-Meteo (``https://api.open-meteo.com/v1/forecast``).

Verified constraints, not assumptions:

* the free Open-Meteo tier needs **no API key**, is limited to
  **non-commercial use** and about 10,000 calls/day, and carries **no uptime
  guarantee** (status: status.open-meteo.com). Commercial use requires a
  customer-prefixed URL and a key -- see ``WEATHER_COMMERCIAL_USE``.
* the API is therefore never trusted to be up. Every failure mode below returns
  an explicit ``available: false`` with a reason. It never substitutes a
  previous reading, a seasonal average, a default value, or a guess.

Coordinates are validated with :mod:`tourist.geo_validation` first, so a
null-island or otherwise unusable fix cannot produce a confident forecast for a
place nobody is in.

Note on "official" alerts: the Department of Hydrology and Meteorology
(dhm.gov.np) publishes forecasts and early warnings on its website and in its
"Nepal Weather Official" app, but exposes **no documented public API or feed**.
This module therefore does not scrape it. Scraping an undocumented government
site would be fragile, and presenting scraped text as a verified official alert
is exactly the kind of claim this project refuses to make. Wire a permitted,
documented feed through the alert provider when one exists.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import requests
from django.conf import settings
from django.core.cache import cache

from .geo_validation import validate_fix

logger = logging.getLogger(__name__)

PROVIDER_SETTING_KEY = "weather_provider"
DEFAULT_PROVIDER_URL = "https://api.open-meteo.com/v1/forecast"

# Set true only when a commercial Open-Meteo plan (customer- prefixed URL plus
# API key) is actually configured. The free tier is non-commercial only.
WEATHER_COMMERCIAL_USE = False

CURRENT_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]

DAILY_FIELDS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "uv_index_max",
    "sunrise",
    "sunset",
    "wind_speed_10m_max",
]

# WMO 4677 weather interpretation codes, as published by Open-Meteo.
WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    97: "Heavy thunderstorm",
    99: "Thunderstorm with heavy hail",
}


def describe_weather_code(code: Any) -> Optional[str]:
    try:
        return WMO_CODES.get(int(code))
    except (TypeError, ValueError):
        return None


def provider_config() -> dict[str, Any]:
    """Resolve the weather provider, admin setting first, environment second.

    HTTPS is required, so a provider can never be silently downgraded to plain
    HTTP for a request that carries no user data but still should not travel
    in the clear.
    """
    from .models import SiteSetting

    row = SiteSetting.objects.filter(key=PROVIDER_SETTING_KEY).first()
    if row is not None and isinstance(row.value, dict):
        base = str(row.value.get("base_url") or "").strip().rstrip("/")
        api_key = str(row.value.get("api_key") or "")
        enabled = bool(row.value.get("enabled", True)) and base.startswith("https://")
        return {
            "enabled": enabled,
            "base_url": base,
            "api_key": api_key,
            "source": "admin_setting",
            "reason": None if enabled else (
                "disabled_by_admin" if not row.value.get("enabled", True)
                else "provider_url_must_be_https"
            ),
        }

    base = (getattr(settings, "WEATHER_API_URL", "") or "").strip().rstrip("/") or DEFAULT_PROVIDER_URL
    api_key = str(getattr(settings, "WEATHER_API_KEY", "") or "")
    enabled = base.startswith("https://")
    return {
        "enabled": enabled,
        "base_url": base,
        "api_key": api_key,
        "source": "environment" if getattr(settings, "WEATHER_API_URL", "") else "default_open_meteo",
        "reason": None if enabled else "weather_provider_url_must_be_https",
    }


@dataclass
class WeatherResult:
    """A weather reading, or an explicit statement that there isn't one."""

    available: bool
    reason: Optional[str] = None
    source: str = ""
    retrieved_at: Optional[str] = None
    current: dict[str, Any] = field(default_factory=dict)
    daily: list[dict[str, Any]] = field(default_factory=list)
    coordinates: Optional[dict[str, Any]] = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "available": self.available,
            "source": self.source,
            "retrieved_at": self.retrieved_at,
        }
        if not self.available:
            payload["reason"] = self.reason
            payload["current"] = {}
            payload["daily"] = []
            return payload
        payload["current"] = self.current
        payload["daily"] = self.daily
        payload["coordinates"] = self.coordinates
        return payload


def _cache_key(latitude: float, longitude: float, days: int) -> str:
    # Round to ~1 km so nearby requests share a cache entry.
    digest = hashlib.sha256(
        f"{latitude:.3f},{longitude:.3f},{days}".encode("utf-8")
    ).hexdigest()[:24]
    return f"weather:v1:{digest}"


def _timeout() -> float:
    return float(getattr(settings, "EXTERNAL_SYNC_TIMEOUT", 5) or 5)


def fetch_weather(
    latitude,
    longitude,
    *,
    forecast_days: int = 3,
    use_cache: bool = True,
    timeout: Optional[float] = None,
) -> WeatherResult:
    """Return current conditions and a short daily forecast, or say why not.

    Never raises for a provider problem: an unreachable or unconfigured
    provider is a normal operating condition for a free tier with no uptime
    guarantee, and the caller must be able to render "unavailable" honestly.
    """
    fix = validate_fix(latitude, longitude, source="weather_lookup")
    if not fix.usable:
        return WeatherResult(
            available=False,
            reason="invalid_coordinates:" + ",".join(fix.reasons or ["unusable"]),
            source="validation",
        )

    config = provider_config()
    if not config["enabled"]:
        return WeatherResult(
            available=False, reason=config["reason"] or "weather_provider_disabled", source="config"
        )

    days = max(1, min(int(forecast_days or 1), 7))
    key = _cache_key(fix.latitude, fix.longitude, days)
    if use_cache:
        cached = cache.get(key)
        if cached:
            return WeatherResult(**cached)

    params = {
        "latitude": fix.latitude,
        "longitude": fix.longitude,
        "current": ",".join(CURRENT_FIELDS),
        "daily": ",".join(DAILY_FIELDS),
        "forecast_days": days,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
    }
    headers = {"Accept": "application/json"}
    if config["api_key"]:
        headers["Authorization"] = f"Bearer {config['api_key']}"

    try:
        response = requests.get(
            config["base_url"],
            params=params,
            headers=headers,
            timeout=timeout or _timeout(),
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout:
        logger.info("weather provider timed out for %s", key)
        return WeatherResult(available=False, reason="provider_timeout", source=config["source"])
    except requests.RequestException as exc:
        logger.warning("weather provider unavailable: %s", exc)
        return WeatherResult(available=False, reason="provider_unavailable", source=config["source"])
    except ValueError:
        return WeatherResult(available=False, reason="provider_invalid_response", source=config["source"])
    except Exception as exc:  # noqa: BLE001
        # A free tier with no uptime guarantee, and TLS/DNS/proxy failures that
        # do not all surface as RequestException. An external provider must
        # never turn a weather banner into a 500.
        logger.warning("unexpected weather provider failure: %s", exc, exc_info=True)
        return WeatherResult(available=False, reason="provider_error", source=config["source"])

    current_block = payload.get("current") or {}
    if not current_block:
        return WeatherResult(available=False, reason="no_current_conditions", source=config["source"])

    code = current_block.get("weather_code")
    current = {
        "time": current_block.get("time"),
        "temperature_c": current_block.get("temperature_2m"),
        "apparent_temperature_c": current_block.get("apparent_temperature"),
        "relative_humidity_pct": current_block.get("relative_humidity_2m"),
        "precipitation_mm": current_block.get("precipitation"),
        "cloud_cover_pct": current_block.get("cloud_cover"),
        "wind_speed_kmh": current_block.get("wind_speed_10m"),
        "wind_gusts_kmh": current_block.get("wind_gusts_10m"),
        "wind_direction_deg": current_block.get("wind_direction_10m"),
        "is_day": current_block.get("is_day"),
        "weather_code": code,
        "description": describe_weather_code(code),
        # Never present a model run as an observation from a station.
        "kind": "model_forecast",
    }

    daily = _build_daily(payload.get("daily") or {})

    result = WeatherResult(
        available=True,
        source=config["source"],
        retrieved_at=current_block.get("time"),
        current=current,
        daily=daily,
        coordinates={
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "elevation_m": payload.get("elevation"),
            "timezone": payload.get("timezone"),
            "requested": {"latitude": fix.latitude, "longitude": fix.longitude},
            "grid_note": "Forecast is for the model grid cell, which may be a few km from the requested point.",
        },
    )
    if use_cache:
        cache.set(key, result.__dict__, 900)
    return result


def _build_daily(daily_block: dict[str, Any]) -> list[dict[str, Any]]:
    times = daily_block.get("time") or []
    if not times:
        return []
    rows = []
    for index, day in enumerate(times):
        code = _at(daily_block.get("weather_code"), index)
        rows.append(
            {
                "date": day,
                "weather_code": code,
                "description": describe_weather_code(code),
                "temperature_max_c": _at(daily_block.get("temperature_2m_max"), index),
                "temperature_min_c": _at(daily_block.get("temperature_2m_min"), index),
                "precipitation_sum_mm": _at(daily_block.get("precipitation_sum"), index),
                "precipitation_probability_max_pct": _at(
                    daily_block.get("precipitation_probability_max"), index
                ),
                "uv_index_max": _at(daily_block.get("uv_index_max"), index),
                "sunrise": _at(daily_block.get("sunrise"), index),
                "sunset": _at(daily_block.get("sunset"), index),
                "wind_speed_max_kmh": _at(daily_block.get("wind_speed_10m_max"), index),
            }
        )
    return rows


def _at(values: Any, index: int):
    if isinstance(values, list) and index < len(values):
        return values[index]
    return None
