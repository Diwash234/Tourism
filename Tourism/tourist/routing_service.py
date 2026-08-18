"""Optional road metrics with an explicit straight-line fallback."""
import hashlib

import requests
from django.conf import settings
from django.core.cache import cache

from .utils import haversine_distance


def route_metrics(start_lat, start_lon, end_lat, end_lon):
    values = list(map(float, (start_lat, start_lon, end_lat, end_lon)))
    straight = round(haversine_distance(*values), 2)
    if not settings.ROUTING_API_URL:
        return {
            "straight_line_km": straight, "road_distance_km": None,
            "duration_min": None, "status": "routing_unconfigured",
            "note": "Road distance unavailable; straight-line distance is not road distance.",
        }
    key_raw = ":".join(f"{value:.5f}" for value in values)
    cache_key = "route-metrics:" + hashlib.sha256(key_raw.encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return cached
    base = settings.ROUTING_API_URL.rstrip("/")
    url = f"{base}/route/v1/driving/{values[1]},{values[0]};{values[3]},{values[2]}"
    headers = {"Accept": "application/json", "User-Agent": "NepalTourismRouting/1.0"}
    if settings.ROUTING_API_KEY:
        headers["Authorization"] = f"Bearer {settings.ROUTING_API_KEY}"
    try:
        response = requests.get(url, params={"overview": "false", "steps": "false"}, headers=headers, timeout=settings.EXTERNAL_SYNC_TIMEOUT)
        response.raise_for_status()
        route = response.json().get("routes", [])[0]
        result = {
            "straight_line_km": straight,
            "road_distance_km": round(float(route["distance"]) / 1000, 2),
            "duration_min": round(float(route["duration"]) / 60),
            "status": "routed", "note": "Road metric supplied by the configured routing service.",
        }
        cache.set(cache_key, result, timeout=1800)
        return result
    except (requests.RequestException, IndexError, KeyError, TypeError, ValueError) as exc:
        return {
            "straight_line_km": straight, "road_distance_km": None,
            "duration_min": None, "status": "routing_unavailable",
            "note": f"Routing service unavailable; showing straight-line distance only. {str(exc)[:120]}",
        }
