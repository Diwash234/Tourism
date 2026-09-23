"""Pure-geometry map matching + off-route detection.

Deliberately dependency-free (no numpy): point-to-segment projection on a
local equirectangular frame, which is accurate to well under a metre for
segment lengths inside Nepal at GPS scale.
"""
from __future__ import annotations

import math

EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _project_point(px: float, py: float, ax: float, ay: float, bx: float, by: float):
    """Project point p onto segment ab in a planar frame; returns (t, x, y)."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return 0.0, ax, ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return t, ax + t * dx, ay + t * dy


def polyline_lengths_m(geometry: list[list[float]]) -> list[float]:
    return [haversine_m(geometry[i][0], geometry[i][1], geometry[i + 1][0], geometry[i + 1][1])
            for i in range(len(geometry) - 1)]


def match_point_to_route(location: tuple[float, float],
                         geometry: list[list[float]]) -> dict:
    """Snap a GPS fix to the route polyline.

    Returns {snapped:[lat,lng], distance_from_route_m, segment_index, t,
    traveled_m} where traveled_m is distance along the route to the snap
    point. Pure geometry — no vendor calls.
    """
    lat, lng = float(location[0]), float(location[1])
    # local planar frame (metres per degree at this latitude)
    m_per_deg_lat = 111320.0
    m_per_deg_lng = 111320.0 * math.cos(math.radians(lat))
    px, py = lng * m_per_deg_lng, lat * m_per_deg_lat

    best = None
    traveled_before = 0.0
    for i in range(len(geometry) - 1):
        a_lat, a_lng = geometry[i]
        b_lat, b_lng = geometry[i + 1]
        ax, ay = a_lng * m_per_deg_lng, a_lat * m_per_deg_lat
        bx, by = b_lng * m_per_deg_lng, b_lat * m_per_deg_lat
        t, sx, sy = _project_point(px, py, ax, ay, bx, by)
        dist = math.hypot(px - sx, py - sy)
        if best is None or dist < best["distance_from_route_m"]:
            seg_len = math.hypot(bx - ax, by - ay)
            best = {
                "distance_from_route_m": dist,
                "segment_index": i,
                "t": t,
                "snapped": [sy / m_per_deg_lat, sx / m_per_deg_lng],
                "traveled_m": traveled_before + t * seg_len,
            }
        traveled_before += math.hypot(bx - ax, by - ay)
    if best is None:
        return {"snapped": [lat, lng], "distance_from_route_m": 0.0,
                "segment_index": 0, "t": 0.0, "traveled_m": 0.0}
    best["distance_from_route_m"] = round(best["distance_from_route_m"], 1)
    best["traveled_m"] = round(best["traveled_m"], 1)
    return best


def off_route_threshold_m(accuracy_m: float | None) -> float:
    """Hysteresis threshold combining GPS accuracy with a floor.

    Plan examples: accuracy 7 m @ 12 m from route -> ON route;
    accuracy 8 m @ 75 m from route -> OFF route.
    threshold = max(30, 4*accuracy): 12 < 30 -> on; 75 > 32 -> off.
    """
    acc = max(0.0, float(accuracy_m)) if accuracy_m is not None else 0.0
    return max(30.0, 4.0 * acc)
