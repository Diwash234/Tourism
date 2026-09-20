"""Live navigation sessions: progress, next instruction, ETA, reroute.

A route session is the canonical route dict plus a route_id, stored in the
Django cache (no restart needed, honours existing cache infrastructure).
Progress requests are pure geometry — no vendor calls — so they stay fast
enough for 5-10 s polling from the browser.
"""
from __future__ import annotations

import uuid

from django.core.cache import cache

from .map_matching import off_route_threshold_m, polyline_lengths_m

SESSION_TTL_S = 2 * 60 * 60
ARRIVAL_RADIUS_M = 30.0


def create_session(route: dict) -> str:
    route_id = uuid.uuid4().hex[:12]
    lengths = polyline_lengths_m(route["geometry"]) if len(route.get("geometry", [])) > 1 else []
    route["_segment_lengths_m"] = lengths
    route["_total_length_m"] = round(sum(lengths), 1)
    # cumulative step distances for next-instruction lookup
    cum, acc = [], 0.0
    for st in route.get("steps", []):
        acc += float(st.get("distance_m", 0))
        cum.append(round(acc, 1))
    route["_step_cumulative_m"] = cum
    cache.set(f"nav-session:{route_id}", route, SESSION_TTL_S)
    return route_id


def get_session(route_id: str) -> dict | None:
    return cache.get(f"nav-session:{route_id}")


def compute_progress(route: dict, latitude: float, longitude: float,
                     heading: float | None = None, accuracy: float | None = None) -> dict:
    from .map_matching import match_point_to_route
    geometry = route.get("geometry") or []
    if len(geometry) < 2:
        return {"on_route": False, "reroute_required": True,
                "error": "route has no geometry"}

    match = match_point_to_route((latitude, longitude), geometry)
    total = route.get("_total_length_m") or sum(polyline_lengths_m(geometry))
    traveled = min(match["traveled_m"], total)
    remaining_m = max(0.0, round(total - traveled, 1))

    duration_total = float(route.get("duration_s") or 0)
    remaining_s = round(duration_total * (remaining_m / total), 1) if total else 0.0

    # next instruction: first step whose cumulative end is beyond traveled
    steps = route.get("steps") or []
    cum = route.get("_step_cumulative_m") or []
    # next instruction = the first upcoming MANEUVER. In OSRM semantics a
    # step's maneuver happens at the step's START, so look at start offsets
    # (cumulative end minus the step's own length), not ends.
    next_instruction = None
    for idx, st in enumerate(steps):
        end = cum[idx] if idx < len(cum) else total
        start_at = max(0.0, end - float(st.get("distance_m", 0)))
        if start_at > traveled + 1:
            next_instruction = {
                "instruction": st.get("instruction"),
                "maneuver": st.get("maneuver"),
                "distance_m": round(start_at - traveled, 1),
            }
            break

    threshold = off_route_threshold_m(accuracy)
    off = match["distance_from_route_m"] > threshold
    arrived = remaining_m <= ARRIVAL_RADIUS_M and not off

    result = {
        "on_route": not off,
        "reroute_required": off and not arrived,
        "arrived": arrived,
        "distance_from_route_m": match["distance_from_route_m"],
        "off_route_threshold_m": threshold,
        "distance_remaining_m": remaining_m,
        "duration_remaining_s": remaining_s,
        "progress": round(traveled / total, 4) if total else 0.0,
        "snapped": match["snapped"],
        "next_instruction": next_instruction,
    }
    if heading is not None:
        result["heading"] = heading
    return result
