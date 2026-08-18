"""Optional road metrics with an explicit straight-line fallback."""
import hashlib

import requests
from django.conf import settings
from django.core.cache import cache

from .utils import haversine_distance


def _local_graph_metrics(values):
    """Route on the bundled GraphML tourism graph (not a street-level road graph)."""
    if not settings.LOCAL_GRAPH_ROUTING_ENABLED:
        return None
    try:
        import sys
        from pathlib import Path
        ml_root = Path(settings.BASE_DIR).parent / "ml_service"
        if str(ml_root) not in sys.path:
            sys.path.insert(0, str(ml_root))
        from model.route.route_engine import best_route
        result = best_route(values[0], values[1], values[2], values[3], "fastest")
        if result.get("error"):
            return None
        max_snap = max(float(result.get("start_snap_km", 0)), float(result.get("end_snap_km", 0)))
        if max_snap > settings.LOCAL_GRAPH_MAX_SNAP_KM:
            return None
        distance = float(result["distance_km"])
        return {
            "straight_line_km": round(haversine_distance(*values), 2),
            "route_distance_km": round(distance, 2),
            "road_distance_km": None,
            "duration_min": max(1, round(distance / 35 * 60)),
            "status": "graph_routed",
            "routing_engine": "bundled_nepal_graphml",
            "route": result.get("route", []),
            "directions": result.get("directions", []),
            "start_snap_km": result.get("start_snap_km"),
            "end_snap_km": result.get("end_snap_km"),
            "note": "Approximate route on the bundled tourism GraphML. It is not a GraphHopper/OSRM street-level road route.",
        }
    except (ImportError, FileNotFoundError, ValueError, TypeError):
        return None


def route_metrics(start_lat, start_lon, end_lat, end_lon):
    values = list(map(float, (start_lat, start_lon, end_lat, end_lon)))
    straight = round(haversine_distance(*values), 2)
    if not settings.ROUTING_API_URL:
        local = _local_graph_metrics(values)
        if local:
            return local
        return {
            "straight_line_km": straight, "route_distance_km": None, "road_distance_km": None,
            "duration_min": None, "status": "routing_unconfigured",
            "note": "No usable local graph path or road-routing service; straight-line distance is not road distance.",
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
            "route_distance_km": round(float(route["distance"]) / 1000, 2),
            "road_distance_km": round(float(route["distance"]) / 1000, 2),
            "duration_min": round(float(route["duration"]) / 60),
            "status": "routed", "note": "Road metric supplied by the configured routing service.",
        }
        cache.set(cache_key, result, timeout=1800)
        return result
    except (requests.RequestException, IndexError, KeyError, TypeError, ValueError) as exc:
        return {
            "straight_line_km": straight, "route_distance_km": None, "road_distance_km": None,
            "duration_min": None, "status": "routing_unavailable",
            "note": f"Routing service unavailable; showing straight-line distance only. {str(exc)[:120]}",
        }
