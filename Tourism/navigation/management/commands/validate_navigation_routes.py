"""Validate REAL road routing on named Nepal routes.

Runs the canonical acceptance set (Pokhara + intercity + walking +
motorcycle) against the configured routing backend and verifies far more
than HTTP 200:

  * road geometry (>= 2 points, sane bbox around the corridor)
  * distance (within a plausible band vs straight-line)
  * duration (> 0 and implies a sane speed)
  * maneuvers (>= 1 step with an instruction)
  * alternatives (requested; count reported — not required to be > 0)
  * source == "osrm" unless --allow-fallback is passed

Usage (on the deployment host with a real OSRM):
    python manage.py validate_navigation_routes
    ROUTING_BASE_URL=http://osrm.internal python manage.py validate_navigation_routes
    python manage.py validate_navigation_routes --allow-fallback   # CI without OSRM
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from navigation import route_engine
from navigation.map_matching import haversine_m

# (label, start, destination, mode) — coordinates of real, named places.
ROUTES = [
    ("Lakeside -> Davis Falls", (28.2096, 83.9856), (28.1834, 83.9762), "driving"),
    ("Lakeside -> World Peace Pagoda", (28.2096, 83.9856), (28.1951, 83.9742), "driving"),
    ("Lakeside -> Sarangkot", (28.2096, 83.9856), (28.2436, 83.9398), "driving"),
    ("Lakeside -> Begnas Lake", (28.2096, 83.9856), (28.1946, 84.0819), "driving"),
    ("Kathmandu -> Pokhara", (27.7172, 85.3240), (28.2096, 83.9856), "driving"),
    ("Lakeside walk (Pame direction)", (28.2096, 83.9856), (28.1845, 83.9770), "walking"),
    ("Lakeside -> Sarangkot (motorcycle)", (28.2096, 83.9856), (28.2436, 83.9398), "motorcycle"),
]


def check_route(label, start, dest, mode, allow_fallback):
    problems = []
    result, _cached = route_engine.cached_route(start, dest, mode, want_alternatives=True,
                                                use_cache=False)
    route = result["route"]
    src = route.get("source")
    if src != "osrm" and not allow_fallback:
        problems.append(f"source={src} (real OSRM required; pass --allow-fallback "
                        "only to exercise the fallback chain)")
    geo = route.get("geometry") or []
    if len(geo) < 2:
        problems.append("geometry has < 2 points")
    else:
        lats = [g[0] for g in geo]
        lngs = [g[1] for g in geo]
        s_lat, e_lat = start[0], dest[0]
        s_lng, e_lng = start[1], dest[1]
        span_lat = max(0.15, abs(e_lat - s_lat) * 2)
        span_lng = max(0.15, abs(e_lng - s_lng) * 2)
        if min(lats) < min(s_lat, e_lat) - span_lat or max(lats) > max(s_lat, e_lat) + span_lat:
            problems.append("geometry latitude escapes the corridor bbox")
        if min(lngs) < min(s_lng, e_lng) - span_lng or max(lngs) > max(s_lng, e_lng) + span_lng:
            problems.append("geometry longitude escapes the corridor bbox")

    straight = haversine_m(start[0], start[1], dest[0], dest[1])
    dist = route.get("distance_m") or 0
    if src == "osrm":
        if not (straight * 0.9 <= dist <= straight * 4 + 5000):
            problems.append(f"distance {dist:.0f}m implausible vs straight-line {straight:.0f}m")
    dur = route.get("duration_s") or 0
    if dur <= 0:
        problems.append("duration <= 0")
    else:
        speed_kmh = (dist / 1000) / (dur / 3600)
        lo, hi = (0.5, 15) if mode in ("walking", "hiking") else (2, 140)
        if not (lo <= speed_kmh <= hi):
            problems.append(f"implied speed {speed_kmh:.1f} km/h outside [{lo},{hi}]")

    steps = route.get("steps") or []
    if not any((s.get("instruction") or "").strip() for s in steps):
        problems.append("no maneuver instructions")

    return {
        "label": label, "source": src, "distance_m": dist, "duration_s": dur,
        "geometry_points": len(geo), "steps": len(steps),
        "alternatives": len(result.get("alternatives") or []),
        "problems": problems,
    }


class Command(BaseCommand):
    help = "Validate real road routing (geometry/distance/duration/maneuvers) on named routes."

    def add_arguments(self, parser):
        parser.add_argument("--allow-fallback", action="store_true",
                            help="Accept labelled fallback sources (CI/dev without OSRM).")

    def handle(self, *args, **options):
        allow = options["allow_fallback"]
        failures = 0
        for label, start, dest, mode in ROUTES:
            r = check_route(label, start, dest, mode, allow)
            status = "PASS" if not r["problems"] else "FAIL"
            if r["problems"]:
                failures += 1
            self.stdout.write(
                f"[{status}] {label} ({mode}) source={r['source']} "
                f"dist={r['distance_m']:.0f}m dur={r['duration_s']:.0f}s "
                f"pts={r['geometry_points']} steps={r['steps']} alts={r['alternatives']}")
            for p in r["problems"]:
                self.stdout.write(self.style.ERROR(f"       - {p}"))
        if failures:
            self.stdout.write(self.style.ERROR(f"{failures} route(s) failed validation"))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            f"all {len(ROUTES)} routes validated "
            f"({'fallback allowed' if allow else 'real OSRM'})"))
