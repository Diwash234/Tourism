"""Provider selection, response caching and simple rate limiting."""
from __future__ import annotations

import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import cache

from .fallback_providers import BundledGraphProvider, StraightLineProvider
from .osrm_provider import OSRMProvider


def get_provider():
    name = (getattr(settings, "ROUTING_PROVIDER", "osrm") or "osrm").lower()
    if name == "osrm":
        return OSRMProvider()
    if name == "bundled_graph":
        return BundledGraphProvider()
    if name == "straight_line":
        return StraightLineProvider()
    return OSRMProvider()


def provider_chain():
    """Ordered fallback chain: configured provider, then graph, then line."""
    primary = get_provider()
    chain = [primary]
    for fallback in (BundledGraphProvider(), StraightLineProvider()):
        if not any(p.name == fallback.name for p in chain):
            chain.append(fallback)
    return chain


logger = logging.getLogger(__name__)


def record_diagnostics(route: dict, mode: str, started: float, alternatives_count: int,
                       start=None, destination=None):
    """Persist a diagnostics row (never break routing if this fails)."""
    try:
        from .models import RouteDiagnostics
        source = route.get("source", "")
        fallback = source != "osrm"
        RouteDiagnostics.objects.create(
            provider=source, mode=mode,
            distance_m=route.get("distance_m"), duration_s=route.get("duration_s"),
            fallback=fallback,
            route_time_ms=int((time.monotonic() - started) * 1000),
            alternatives=alternatives_count,
            start_lat=start[0] if start else None, start_lng=start[1] if start else None,
            dest_lat=destination[0] if destination else None,
            dest_lng=destination[1] if destination else None,
        )
        if fallback:
            logger.warning("navigation fallback used: source=%s mode=%s — real road "
                           "routing unavailable (check ROUTING_BASE_URL)", source, mode)
    except Exception as exc:  # diagnostics must never break routing
        logger.error("route diagnostics failed: %s", exc)


def cache_key_for(start, destination, mode) -> str:
    raw = f"{start[0]:.5f},{start[1]:.5f};{destination[0]:.5f},{destination[1]:.5f};{mode}"
    return "nav-route:" + hashlib.sha256(raw.encode()).hexdigest()


_COMPASS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]


def _bearing(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dl = lo2 - lo1
    y = math.sin(dl) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def _dist_m(a, b):
    import math
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def build_maneuvers(route: dict, max_steps: int = 200) -> list:
    """Turn-by-turn steps computed FROM THE ROUTE'S REAL GEOMETRY.

    Bearing changes at actual geometry vertices become instructions — nothing
    is invented. Honesty grades: 'street' when the geometry is OSRM
    street-level, 'corridor-node' for the bundled tourism graph (node-level
    guidance), and straight-line fallback gets a single explicit non-guidance
    step instead of fabricated directions.
    """
    geom = route.get("geometry") or []
    source = route.get("source", "")
    if source == "straight_line_fallback" or len(geom) < 2:
        return [{
            "instruction": ("Straight-line estimate — no road route exists to this remote "
                            "destination; turn-by-turn guidance is not available"),
            "point": list(geom[0]) if geom else None,
            "distance_m": route.get("distance_m"),
            "maneuver_grade": "none",
            "turn": "straight",
        }]
    grade = "street" if source == "osrm" else "corridor-node"

    legs = [(_dist_m(geom[i], geom[i + 1]), _bearing(geom[i], geom[i + 1]))
            for i in range(len(geom) - 1)]

    def _compass(deg):
        return _COMPASS[int(((deg + 22.5) % 360) // 45)]

    def _word(turn):
        a = abs(turn)
        if a >= 120:
            return "turn sharp left" if turn < 0 else "turn sharp right"
        if a >= 70:
            return "turn left" if turn < 0 else "turn right"
        return "turn slight left" if turn < 0 else "turn slight right"

    steps = []
    acc = [0.0]

    def _turn_key(angle):
        """Structured maneuver key for UI icons (left/right/straight/…)."""
        if angle is None:
            return "start"
        a = abs(angle)
        if a >= 150:
            return "uturn"
        if a >= 120:
            return "sharp_left" if angle < 0 else "sharp_right"
        if a >= 70:
            return "left" if angle < 0 else "right"
        return "left" if angle < 0 else "right"  # slight turns use the same icon

    def _push(instruction, point, angle=None, turn_key=None):
        if steps:
            steps[-1]["distance_m"] = round(acc[0])
        steps.append({"instruction": instruction, "point": list(point),
                      "distance_m": 0, "maneuver_grade": grade,
                      "turn": turn_key or _turn_key(angle)})
        acc[0] = 0.0

    _push(f"Head {_compass(legs[0][1])}", geom[0], turn_key="start")
    acc[0] += legs[0][0]
    for i in range(1, len(legs)):
        turn = (legs[i][1] - legs[i - 1][1] + 540) % 360 - 180
        if abs(turn) >= 30 and len(steps) < max_steps:
            _push(_word(turn), geom[i], angle=turn)
        acc[0] += legs[i][0]
    if len(steps) < max_steps:
        _push("Arrive at destination", geom[-1], turn_key="arrive")
    else:
        steps[-1]["instruction"] += " — then continue to destination"
    return steps


def cached_route(start, destination, mode, request=None, want_alternatives=False,
                 use_cache=True):
    """Route with caching + rate limiting. Returns (route_dict, cached: bool).

    Rate limit: ROUTING_RATE_LIMIT requests/minute per IP (default 30),
    enforced via a cache counter. Raises RateLimited.
    """
    limit = int(getattr(settings, "ROUTING_RATE_LIMIT", 30))
    if limit > 0 and request is not None:
        ip = request.META.get("REMOTE_ADDR", "anon")
        bucket = f"nav-rl:{ip}:{int(time.time() // 60)}"
        count = cache.get_or_set(bucket, 0, 120)
        if count >= limit:
            raise RateLimited()
        cache.set(bucket, count + 1, 120)

    key = cache_key_for(start, destination, mode) + (":alt" if want_alternatives else "")
    ttl = int(getattr(settings, "ROUTING_CACHE_TTL", 600))
    if use_cache:
        hit = cache.get(key)
        if hit:
            return hit, True

    started = time.monotonic()

    route = None
    for provider in provider_chain():
        if not provider.supports(mode):
            continue
        route = provider.route(start, destination, mode)
        if route:
            break
    if route is None:
        # last-resort: straight line always answers (never fabricates roads)
        route = StraightLineProvider().route(start, destination, mode)
    route.setdefault("steps", build_maneuvers(route))

    result = {"route": route, "alternatives": []}
    if want_alternatives:
        provider = get_provider()
        if provider.supports(mode):
            result["alternatives"] = provider.alternatives(start, destination, mode)
    record_diagnostics(route, mode, started, len(result["alternatives"]),
                       start=start, destination=destination)
    cache.set(key, result, ttl)
    return result, False


class RateLimited(Exception):
    pass
