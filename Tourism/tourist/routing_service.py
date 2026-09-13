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


def _step_instruction(step):
    """OSRM step -> human instruction. Road names come from the routing
    provider's data, never invented."""
    maneuver = step.get("maneuver") or {}
    mtype = (maneuver.get("type") or "").replace("_", " ")
    modifier = maneuver.get("modifier") or ""
    name = (step.get("name") or "").strip()
    distance_m = int(step.get("distance") or 0)
    if mtype == "depart":
        text = "Head out" + (f" on {name}" if name else "")
    elif mtype == "arrive":
        text = "Arrive at your destination"
    elif mtype == "roundabout" or mtype == "rotary":
        text = f"At the roundabout, take exit {maneuver.get('exit', '')} " + (f"onto {name}" if name else "").strip()
    elif modifier and modifier.lower() != "straight":
        text = f"Turn {modifier.lower()}" + (f" onto {name}" if name else "")
    elif mtype in ("new name", "continue", "fork", "merge", "on ramp", "off ramp"):
        text = ("Continue" if not name else f"Continue onto {name}")
    else:
        text = "Continue straight" + (f" on {name}" if name else "")
    return {"instruction": text.strip(), "distance_m": distance_m,
            "duration_min": round(float(step.get("duration") or 0) / 60, 1),
            "road": name or None}


def route_steps(start_lat, start_lon, end_lat, end_lon):
    """Turn-by-turn steps + geometry when a live provider is configured.
    Returns None otherwise — the UI must say detailed directions require a
    live road-routing provider, never fabricate them."""
    values = list(map(float, (start_lat, start_lon, end_lat, end_lon)))
    provider = provider_config()
    if not provider["enabled"]:
        return None
    url = f"{provider['base_url']}/route/v1/driving/{values[1]},{values[0]};{values[3]},{values[2]}"
    headers = {"Accept": "application/json", "User-Agent": "NepalTourismRouting/1.0"}
    if provider["api_key"]:
        headers["Authorization"] = f"Bearer {provider['api_key']}"
    try:
        response = requests.get(
            url,
            params={"overview": "full", "steps": "true", "geometries": "geojson"},
            headers=headers,
            timeout=settings.EXTERNAL_SYNC_TIMEOUT,
        )
        response.raise_for_status()
        route = response.json().get("routes", [])[0]
        steps = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                steps.append(_step_instruction(step))
        return {
            "source": "routing_provider",
            "distance_km": round(float(route["distance"]) / 1000, 2),
            "duration_min": round(float(route["duration"]) / 60),
            "geometry": (route.get("geometry") or {}).get("coordinates"),
            "steps": steps,
        }
    except (requests.RequestException, IndexError, KeyError, TypeError, ValueError):
        return None


def _route_signature(coords):
    """Coarse shape signature used to discard alternatives identical to the
    primary route (same corridor, same waypoints at ~100 m resolution).
    Accepts {lat,lng} dicts and [lat,lng] arrays alike."""
    signature = []
    for point in (coords or []):
        if isinstance(point, dict):
            lat, lng = point.get("lat"), point.get("lng")
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            lat, lng = point[0], point[1]
        else:
            continue
        try:
            signature.append((round(float(lat), 3), round(float(lng), 3)))
        except (TypeError, ValueError):
            continue
    return tuple(signature)


def _graph_alternatives(values, primary_route_type, primary_signature):
    """Alternatives on the bundled GraphML: same endpoints, different
    optimization weightings (safest/cheapest). Honestly labelled as
    coordinate-based; identical corridors are discarded, never padded."""
    if not settings.LOCAL_GRAPH_ROUTING_ENABLED:
        return []
    try:
        import sys
        from pathlib import Path
        ml_root = Path(settings.BASE_DIR).parent / "ml_service"
        if str(ml_root) not in sys.path:
            sys.path.insert(0, str(ml_root))
        from model.route.route_engine import best_route
    except (ImportError, FileNotFoundError):
        return []
    type_speeds = {"safest": 35, "cheapest": 30}
    alternatives = []
    seen = {primary_signature}
    for alt_type in ("safest", "cheapest"):
        if alt_type == primary_route_type or len(alternatives) >= 2:
            continue
        try:
            result = best_route(values[0], values[1], values[2], values[3], alt_type)
        except (ValueError, TypeError):
            continue
        if result.get("error"):
            continue
        coords = result.get("route", [])
        signature = _route_signature(coords)
        if len(coords) < 2 or not signature or signature in seen:
            continue
        seen.add(signature)
        distance = float(result.get("distance_km") or 0)
        alternatives.append({
            "label": f"{alt_type.title()}-weighted alternative",
            "route": coords,
            "distance_km": round(distance, 2),
            "duration_min": max(1, round(distance / type_speeds[alt_type] * 60)),
            "duration_source": "estimated",
            "duration_note": f"Estimated at ~{type_speeds[alt_type]:g} km/h average; not a live traffic prediction.",
            "routing_engine": "bundled_nepal_graphml",
            "note": "Approximate alternative on the bundled tourism GraphML — coordinate-based, not street-level.",
        })
    return alternatives


def route_alternatives(start_lat, start_lon, end_lat, end_lon,
                       primary_route_type="fastest", primary_route=None):
    """Alternative routes for the Phase-2 selector.

    Provider configured: ask it for OSRM-style ``alternatives=true`` routes
    (street-level steps included). Otherwise: re-route the bundled graph with
    different weightings. Always [] rather than fabricated variety.
    """
    values = list(map(float, (start_lat, start_lon, end_lat, end_lon)))
    provider = provider_config()
    if provider["enabled"]:
        url = f"{provider['base_url']}/route/v1/driving/{values[1]},{values[0]};{values[3]},{values[2]}"
        headers = {"Accept": "application/json", "User-Agent": "NepalTourismRouting/1.0"}
        if provider["api_key"]:
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        try:
            response = requests.get(
                url,
                params={"overview": "full", "steps": "true", "geometries": "geojson", "alternatives": "true"},
                headers=headers,
                timeout=settings.EXTERNAL_SYNC_TIMEOUT,
            )
            response.raise_for_status()
            alternatives = []
            for route in response.json().get("routes", [])[1:3]:
                steps = [
                    _step_instruction(step)
                    for leg in route.get("legs", [])
                    for step in leg.get("steps", [])
                ]
                coords = (route.get("geometry") or {}).get("coordinates") or []
                alternatives.append({
                    "label": "Provider alternative",
                    "route": [{"lat": c[1], "lng": c[0]} for c in coords],
                    "distance_km": round(float(route["distance"]) / 1000, 2),
                    "duration_min": round(float(route["duration"]) / 60),
                    "duration_source": "routing_provider",
                    "steps": steps,
                    "routing_engine": "osrm_protocol_provider",
                })
            return alternatives
        except (requests.RequestException, IndexError, KeyError, TypeError, ValueError):
            pass  # provider configured but failing: degrade exactly like the
            # primary route does — to the labelled bundled graph, never to
            # fabricated variety.
    return _graph_alternatives(values, primary_route_type, _route_signature(primary_route))
