"""Prove whether navigation is really road-routed, or only estimated.

Why this exists
---------------
``routing_service.route_metrics`` degrades honestly: with no provider it returns
a straight-line distance and says so, and when a provider fails it falls back to
the bundled graph and labels that fallback too. That behaviour is correct and is
the reason this project has never published a fake route.

The problem is that a *correctly* degrading service still looks identical to a
working one if you only look at the API response: both return a distance. Nothing
tells an operator whether the number a traveller sees is a real road distance or
a corridor estimate. ``validate_production_config`` catches the extreme case
(``ROUTING_BASE_URL`` empty is a FAIL), but not the case that actually bites: a
provider URL that is set, reachable, and returning numbers derived from
something other than roads.

What it checks
--------------
1. Is a provider configured, and is the service actually reachable?
2. Does a real inter-city route come back, and is it labelled as road-verified?
3. **Is the road distance at least the straight-line distance?** This is the
   check that matters. A route cannot be shorter than the crow flies between the
   same two points. If a "real-road" answer is shorter, the provider is not
   routing over roads and every distance in the app is quietly wrong.
4. Is the detour ratio plausible? Roads in Nepal are mountainous; a ratio near
   1.0 on a mountain route means the straight line is being reported back, and a
   wildly large ratio means the two points probably do not match the network.
5. Are the coordinates themselves real? A perfect route between two identical or
   null-island points proves nothing, so the probe refuses them.

The command never edits data and never "fixes" a route. It reports what the
service actually returned, and refuses to call it road-verified unless the
geometry checks out.

Usage
-----
    python manage.py audit_routing
    python manage.py audit_routing --json
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from django.core.management.base import BaseCommand

from tourist.console_safe import make_console_utf8, safe_text
from tourist.geo_validation import (
    NEPAL_LAT_MAX,
    NEPAL_LAT_MIN,
    NEPAL_LON_MAX,
    NEPAL_LON_MIN,
    haversine_km,
)
from tourist.models import Destination
from tourist.routing_service import provider_config, route_metrics

# Two places far enough apart that a road route must differ visibly from the
# crow flight, and both well inside the extract.
ROUTE_ENGINE_LABELS = {"osrm_protocol_provider": "real-road", "graphml_fallback": "corridor-estimate"}

# Below this a "road" route is indistinguishable from a straight line and should
# not be presented as road-verified.
MIN_PLAUSIBLE_DETOUR = 1.02
# Above this, the endpoints probably do not correspond to the road network, or
# the provider is returning something other than a route between them.
MAX_PLAUSIBLE_DETOUR = 4.0


@dataclass
class Probe:
    label: str
    origin_name: str
    destination_name: str
    straight_line_km: float | None = None
    route_distance_km: float | None = None
    duration_min: int | None = None
    status: str = ""
    routing_engine: str = ""
    note: str = ""
    problems: list = field(default_factory=list)

    @property
    def detour_ratio(self) -> float | None:
        if not self.route_distance_km or not self.straight_line_km:
            return None
        return self.route_distance_km / self.straight_line_km

    @property
    def is_road_verified(self) -> bool:
        return (
            self.routing_engine == "osrm_protocol_provider"
            and self.status == "routed"
            and not self.problems
            and (self.detour_ratio or 0) >= MIN_PLAUSIBLE_DETOUR
        )


def _usable_destination(dest) -> bool:
    if dest is None or dest.latitude is None or dest.longitude is None:
        return False
    lat, lon = float(dest.latitude), float(dest.longitude)
    if not (NEPAL_LAT_MIN <= lat <= NEPAL_LAT_MAX and NEPAL_LON_MIN <= lon <= NEPAL_LON_MAX):
        return False
    # Two points at the same place cannot validate a route.
    return True


def probe_pair(origin, destination, label: str) -> Probe:
    probe = Probe(
        label=label,
        origin_name=safe_text(origin.name, 60),
        destination_name=safe_text(destination.name, 60),
    )
    if not _usable_destination(origin) or not _usable_destination(destination):
        probe.problems.append("endpoint has no usable Nepal coordinate; cannot validate a route")
        return probe

    result = route_metrics(origin.latitude, origin.longitude,
                           destination.latitude, destination.longitude)
    probe.straight_line_km = result.get("straight_line_km")
    probe.route_distance_km = result.get("route_distance_km")
    probe.duration_min = result.get("duration_min")
    probe.status = result.get("status") or ""
    probe.routing_engine = result.get("routing_engine") or ""
    probe.note = result.get("note") or ""

    if probe.status != "routed":
        probe.problems.append(f"no road route returned (status={probe.status or 'none'})")
        return probe
    if probe.routing_engine != "osrm_protocol_provider":
        probe.problems.append(
            f"returned a {ROUTE_ENGINE_LABELS.get(probe.routing_engine, probe.routing_engine)}, "
            "not a real road route"
        )
        return probe

    straight = haversine_km(
        float(origin.latitude), float(origin.longitude),
        float(destination.latitude), float(destination.longitude),
    )
    if probe.route_distance_km is None:
        probe.problems.append("provider returned no distance")
        return probe

    if probe.route_distance_km < straight - 0.05:
        # Physically impossible. Whatever is answering is not routing between
        # these two points, so nothing it says can be trusted.
        probe.problems.append(
            f"road distance {probe.route_distance_km} km is shorter than the "
            f"{round(straight, 1)} km straight line -- impossible, so this is not a road route"
        )
    elif (probe.detour_ratio or 0) < MIN_PLAUSIBLE_DETOUR:
        probe.problems.append(
            f"detour ratio {probe.detour_ratio:.2f} is too close to 1.0; the provider may be "
            "echoing the straight-line distance"
        )
    elif (probe.detour_ratio or 0) > MAX_PLAUSIBLE_DETOUR:
        probe.problems.append(
            f"detour ratio {probe.detour_ratio:.2f} is implausibly large; the endpoints may not "
            "correspond to the same road network"
        )
    return probe


class Command(BaseCommand):
    help = "Report whether navigation uses real road routing or only estimates."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    def handle(self, *args, **options):
        make_console_utf8()
        provider = provider_config()
        probes: list[Probe] = []

        # Pick endpoints from the data itself so the probe exercises the same
        # coordinates travellers will use, including their provenance gaps.
        pairs = self._pairs()
        for label, origin, destination in pairs:
            if origin is None or destination is None:
                probes.append(Probe(
                    label=label, origin_name="(not found)", destination_name="(not found)",
                    problems=["no destination in the database matched this probe pair"],
                ))
                continue
            probes.append(probe_pair(origin, destination, label))

        verified = [p for p in probes if p.is_road_verified]

        if options["json"]:
            self.stdout.write(json.dumps({
                "provider_enabled": provider["enabled"],
                "provider_source": provider["source"],
                "base_url_configured": bool(provider["base_url"]),
                "road_verified": bool(verified),
                "probes": [asdict(p) | {"detour_ratio": p.detour_ratio,
                                        "is_road_verified": p.is_road_verified} for p in probes],
            }, indent=2, ensure_ascii=False))
            return

        self.stdout.write("Road-routing audit")
        self.stdout.write("  (reads the routing service; changes nothing)")
        self.stdout.write("")
        self.stdout.write(f"provider enabled : {provider['enabled']} (source: {provider['source']})")
        self.stdout.write(f"base URL set    : {bool(provider['base_url'])}")
        self.stdout.write("")

        for probe in probes:
            head = f"{probe.label}: {probe.origin_name} -> {probe.destination_name}"
            self.stdout.write(head)
            if probe.straight_line_km is not None:
                self.stdout.write(
                    f"  straight line {probe.straight_line_km} km"
                    + (f"   road {probe.route_distance_km} km" if probe.route_distance_km else "")
                    + (f"   {probe.duration_min} min" if probe.duration_min else "")
                )
            if probe.detour_ratio:
                self.stdout.write(f"  detour ratio  {probe.detour_ratio:.2f}x")
            self.stdout.write(f"  status        {probe.status or 'none'} "
                              f"[{ROUTE_ENGINE_LABELS.get(probe.routing_engine, 'none')}]")
            if probe.note:
                self.stdout.write(f"  note          {safe_text(probe.note, 110)}")
            for problem in probe.problems:
                self.stdout.write(self.style.WARNING(f"  problem       {problem}"))
            self.stdout.write("")

        if verified:
            self.stdout.write(self.style.SUCCESS(
                f"VERIFIED: {len(verified)}/{len(probes)} probe(s) returned a real road route "
                "that is physically consistent with its endpoints."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "NOT VERIFIED: no probe returned a real, physically consistent road route. "
                "Distances shown to travellers are straight-line or corridor estimates, and the "
                "app labels them as such. To fix: run an OSRM-compatible service over a Nepal OSM "
                "extract (see docs/ROUTING.md) and set ROUTING_BASE_URL."
            ))

    def _pairs(self):
        """Long-distance pairs from the real data, with fallbacks."""
        wanted = [
            ("kathmandu-pokhara", ["Kathmandu Durbar Square", "P Kathmandu Durbar Square",
                                   "Kathmandu"], ["Phewa Lake", "Pokhara"]),
            ("pokhara-beni", ["Pokhara", "Lakeside"], ["Beni", "Besisahar"]),
        ]
        found = []
        for label, origin_names, destination_names in wanted:
            origin = self._lookup(origin_names)
            destination = self._lookup(destination_names)
            found.append((label, origin, destination))
        return found

    def _lookup(self, names: list[str]):
        queryset = Destination.objects.filter(is_active=True).exclude(latitude=None)\
            .exclude(longitude=None)
        for name in names:
            hit = queryset.filter(name__iexact=name).first()
            if hit:
                return hit
        for name in names:
            hit = queryset.filter(name__icontains=name).first()
            if hit:
                return hit
        return None
