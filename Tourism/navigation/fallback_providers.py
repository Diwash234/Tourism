"""Offline fallback providers — honest estimates, clearly labelled.

When no OSRM-compatible server is configured/reachable the navigation
endpoint must still answer (graceful fallback, plan item 23), but it must
never pretend an estimate is a road route. `source` and `note` say exactly
what the client is getting:

- BundledGraphProvider (graphml_fallback): routes on the bundled tourism
  GraphML (node-level, NOT street level).
- StraightLineProvider (straight_line_fallback): last resort — one segment,
  haversine distance, conservative duration. NOT navigation-grade routing.
"""
from __future__ import annotations

import math

from django.conf import settings

from .map_matching import haversine_m
from .routing_provider import RoutingProvider

SPEED_MPS = {"driving": 9.7, "motorcycle": 9.7, "walking": 1.3, "hiking": 1.1, "cycling": 4.5}


def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def compass(bearing: float) -> str:
    names = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    return names[int((bearing + 22.5) % 360 // 45)]


def _maneuver_from_instruction(text: str, first: bool) -> str:
    """Map engine instruction text to a stable maneuver key for the UI."""
    t = (text or "").lower()
    if first or t.startswith("head"):
        return "depart"
    if "u-turn" in t or "uturn" in t:
        return "uturn"
    if "sharp left" in t:
        return "turn-sharp-left"
    if "sharp right" in t:
        return "turn-sharp-right"
    if "slight left" in t:
        return "turn-slight-left"
    if "slight right" in t:
        return "turn-slight-right"
    if "left" in t:
        return "turn-left"
    if "right" in t:
        return "turn-right"
    if "straight" in t or "continue" in t:
        return "continue"
    return "continue"


class BundledGraphProvider(RoutingProvider):
    name = "bundled_graph"
    supported_modes = ("driving", "motorcycle", "walking", "hiking", "cycling")

    def route(self, start, destination, mode):
        if not getattr(settings, "LOCAL_GRAPH_ROUTING_ENABLED", False):
            return None
        try:
            import sys
            from pathlib import Path
            ml_root = Path(settings.BASE_DIR).parent / "ml_service"
            if str(ml_root) not in sys.path:
                sys.path.insert(0, str(ml_root))
            from model.route.route_engine import best_route
            result = best_route(start[0], start[1], destination[0], destination[1], "fastest")
            if result.get("error"):
                return None
            nodes = result.get("route") or []
            # route points are dicts {'lat','lng'} (defensively accept pairs too)
            geometry = []
            for n in nodes:
                if isinstance(n, dict) and "lat" in n and "lng" in n:
                    geometry.append([float(n["lat"]), float(n["lng"])])
                elif isinstance(n, (list, tuple)) and len(n) >= 2:
                    geometry.append([float(n[0]), float(n[1])])
            if len(geometry) < 2:
                return None
            speed = SPEED_MPS.get(mode, SPEED_MPS["driving"])
            distance_m = float(result["distance_km"]) * 1000.0

            # Real per-waypoint turn-by-turn from the graph engine, enriched
            # with the landmark names of the corridor nodes we pass.
            path_names = result.get("path") or []
            directions = result.get("directions") or []
            steps = []
            for i, d in enumerate(directions):
                text = str(d.get("instruction") or "").strip()
                seg_m = round(float(d.get("distance_km") or 0.0) * 1000.0, 1)
                maneuver = _maneuver_from_instruction(text, i == 0)
                landmark = path_names[i + 1] if i + 1 < len(path_names) else None
                instruction = text or f"Heading {compass(bearing_deg(*geometry[0], *geometry[1]))}"
                if landmark and maneuver not in ("depart", "arrive"):
                    instruction = f"{instruction} toward {landmark}"
                steps.append({
                    "instruction": instruction,
                    "distance_m": seg_m,
                    "duration_s": round(seg_m / speed, 1),
                    "maneuver": maneuver,
                    "point": geometry[i] if i < len(geometry) else None,
                })
            steps.append({
                "instruction": "Arrive at destination",
                "distance_m": 0.0, "duration_s": 0.0, "maneuver": "arrive",
                "point": geometry[-1],
            })
            lats = [g[0] for g in geometry]
            lngs = [g[1] for g in geometry]
            return {
                "source": "graphml_fallback",
                "mode": mode,
                "distance_m": round(distance_m, 1),
                "duration_s": round(distance_m / speed, 1),
                "geometry": geometry,
                "bounds": [[min(lats), min(lngs)], [max(lats), max(lngs)]],
                "steps": steps,
                "note": ("Approximate route on the bundled tourism GraphML — "
                         "node-level, not a street-level road route."),
            }
        except Exception:
            return None


class StraightLineProvider(RoutingProvider):
    name = "straight_line"
    supported_modes = ("driving", "motorcycle", "walking", "hiking", "cycling")

    def route(self, start, destination, mode):
        distance_m = haversine_m(start[0], start[1], destination[0], destination[1])
        if mode in ("driving", "motorcycle", "cycling"):
            distance_m *= 1.3  # typical road detour factor — still an estimate
        speed = SPEED_MPS.get(mode, SPEED_MPS["driving"])
        geometry = [[start[0], start[1]], [destination[0], destination[1]]]
        return {
            "source": "straight_line_fallback",
            "mode": mode,
            "distance_m": round(distance_m, 1),
            "duration_s": round(distance_m / speed, 1),
            "geometry": geometry,
            "bounds": [[min(start[0], destination[0]), min(start[1], destination[1])],
                       [max(start[0], destination[0]), max(start[1], destination[1])]],
            "steps": [{
                "instruction": f"Head {compass(bearing_deg(*start, *destination))} (straight-line estimate)",
                "distance_m": round(distance_m, 1),
                "duration_s": round(distance_m / speed, 1),
                "maneuver": "depart",
            }, {
                "instruction": "Arrive at destination (estimate)",
                "distance_m": 0.0, "duration_s": 0.0, "maneuver": "arrive",
            }],
            "note": ("Road routing unavailable — this is a straight-line "
                     "estimate, NOT a road route. Enable ROUTING_BASE_URL "
                     "for real turn-by-turn navigation."),
        }
