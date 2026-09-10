"""Road metrics with an admin-configurable provider and honest fallbacks.

Order of truth (master spec §6/§69):
  1. The admin-configured road-routing provider (SiteSetting
     ``routing_provider``, HTTPS base URLs only — no code or deploy needed).
  2. The bundled tourism GraphML graph — explicitly labelled as an
     approximation, never presented as street-level road distance.
  3. Straight-line distance — explicitly labelled as NOT road distance.

Haversine output is never returned as road distance in any branch.
"""
import hashlib

import requests
from django.conf import settings
from django.core.cache import cache

from .utils import haversine_distance

PROVIDER_SETTING_KEY = "routing_provider"


def provider_config():
    """Resolve the road-routing provider.

    The admin SiteSetting wins over the environment so the provider can be
    swapped or disabled without a code change. Only HTTPS base URLs are
    accepted from the setting — a provider can never be downgraded to HTTP.
    Value shape: {"enabled": bool, "base_url": "https://.../route/v1/driving",
                  "api_key": "optional bearer token"}.
    """
    from .models import SiteSetting

    row = SiteSetting.objects.filter(key=PROVIDER_SETTING_KEY).first()
    if row is not None and isinstance(row.value, dict):
        base = str(row.value.get("base_url") or "").strip().rstrip("/")
        api_key = str(row.value.get("api_key") or "")
        enabled = bool(row.value.get("enabled", True)) and base.startswith("https://")
        return {"enabled": enabled, "base_url": base, "api_key": api_key, "source": "admin_setting"}
    base = (getattr(settings, "ROUTING_API_URL", "") or "").strip().rstrip("/")
    api_key = getattr(settings, "ROUTING_API_KEY", "") or ""
    return {"enabled": bool(base), "base_url": base, "api_key": api_key, "source": "environment"}


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
    provider = provider_config()

    if not provider["enabled"]:
        local = _local_graph_metrics(values)
        if local:
            return local
        return {
            "straight_line_km": straight, "route_distance_km": None, "road_distance_km": None,
            "duration_min": None, "status": "routing_unconfigured",
            "routing_engine": None,
            "note": "No road-routing provider configured (admin: site setting 'routing_provider'); "
                    "straight-line distance is not road distance.",
        }

    # Cache per coordinate pair AND provider, so switching providers in the
    # admin panel takes effect immediately instead of serving stale routes.
    key_raw = provider["base_url"] + ":" + ":".join(f"{value:.5f}" for value in values)
    cache_key = "route-metrics:" + hashlib.sha256(key_raw.encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{provider['base_url']}/route/v1/driving/{values[1]},{values[0]};{values[3]},{values[2]}"
    headers = {"Accept": "application/json", "User-Agent": "NepalTourismRouting/1.0"}
    if provider["api_key"]:
        headers["Authorization"] = f"Bearer {provider['api_key']}"
    try:
        response = requests.get(url, params={"overview": "false", "steps": "false"}, headers=headers, timeout=settings.EXTERNAL_SYNC_TIMEOUT)
        response.raise_for_status()
        route = response.json().get("routes", [])[0]
        result = {
            "straight_line_km": straight,
            "route_distance_km": round(float(route["distance"]) / 1000, 2),
            "road_distance_km": round(float(route["distance"]) / 1000, 2),
            "duration_min": round(float(route["duration"]) / 60),
            "status": "routed",
            "routing_engine": "osrm_protocol_provider",
            "provider_source": provider["source"],
            "note": "Road metric supplied by the configured routing service.",
        }
        cache.set(cache_key, result, timeout=1800)
        return result
    except (requests.RequestException, IndexError, KeyError, TypeError, ValueError) as exc:
        # Provider failed: degrade to the bundled graph (clearly labelled as
        # an approximation), and only then to honestly-labelled straight line.
        local = _local_graph_metrics(values)
        if local:
            local["note"] += " The configured road-routing provider failed; this is the bundled-graph approximation, not a street-level route."
            local["provider_source"] = provider["source"]
            return local
        return {
            "straight_line_km": straight, "route_distance_km": None, "road_distance_km": None,
            "duration_min": None, "status": "routing_unavailable",
            "routing_engine": None,
            "note": f"Routing service unavailable; showing straight-line distance only, which is not road distance. {str(exc)[:120]}",
        }
