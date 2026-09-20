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
