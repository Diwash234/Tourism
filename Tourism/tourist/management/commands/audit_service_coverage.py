"""
audit_service_coverage — the accurate, complete method for the owner question
"does EVERY destination have a route, hospital, bank, hotel, restaurant and
police station nearby?"

For all active destinations (currently ~6.6k) it computes:

* routable      — destination has coordinates (a route can be computed);
* nearest km    — to the closest hospital / police / bank / hotel / restaurant
                  (haversine over the real DB tables: Hospital, PoliceStation,
                  OSMEssentialService[bank], Hotel, Restaurant);
* coverage      — share of destinations with each service within 10 / 25 / 50 km;
* hard gaps     — destinations with NO service of a category within 50 km,
                  listed per district in the JSON/CSV output.

Nothing is fetched over the network and nothing is fabricated: distances come
from the same tables the public /places/nearby/ endpoint falls back to, so the
audit measures exactly what a tourist would be told.

Usage:  python manage.py audit_service_coverage [--radius 50]
Writes: reports/service_coverage.json + reports/service_coverage_gaps.csv
"""

import csv
import json
import math
import os
from collections import defaultdict

from django.core.management.base import BaseCommand

from tourist.models import (
    Destination, Hospital, Hotel, OSMEssentialService, PoliceStation, Restaurant,
)

RADII = (10, 25, 50)


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class _Grid:
    """1-degree grid index for fast nearest-neighbour lookups."""

    def __init__(self, rows):
        self.cells = defaultdict(list)
        for name, lat, lng in rows:
            self.cells[(int(lat), int(lng))].append((name, float(lat), float(lng)))

    def nearest(self, lat, lng):
        best = (None, None)
        la, lo = float(lat), float(lng)
        for dlat in (-1, 0, 1):
            for dlng in (-1, 0, 1):
                for name, pla, plo in self.cells.get((int(la) + dlat, int(lo) + dlng), ()):
                    km = _haversine(la, lo, pla, plo)
                    if best[1] is None or km < best[1]:
                        best = (name, km)
        # 3x3 cells (~111 km) is far beyond the 50 km audit radius
        return best


class Command(BaseCommand):
    help = "Audit every destination for route + hospital/bank/hotel/restaurant/police coverage."

    def add_arguments(self, parser):
        parser.add_argument("--radius", type=float, default=50)

    def handle(self, *args, **opts):
        radius = opts["radius"]

        def rows(qs, name_field="name"):
            return [
                (getattr(o, name_field), o.latitude, o.longitude)
                for o in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            ]

        # hospital/police grids = curated tables + the OSM amenity layer,
        # mirroring exactly what /places/nearby/ falls back to
        hospital_rows = rows(Hospital.objects.filter(is_archived=False)) + rows(
            OSMEssentialService.objects.filter(category="hospital", is_archived=False))
        police_rows = rows(PoliceStation.objects.all()) + rows(
            OSMEssentialService.objects.filter(category="police", is_archived=False))
        grids = {
            "hospital": _Grid(hospital_rows),
            "police": _Grid(police_rows),
            "bank": _Grid(rows(OSMEssentialService.objects.filter(category="bank", is_archived=False))),
            "hotel": _Grid(rows(Hotel.objects.filter(is_active=True))),
            "restaurant": _Grid(rows(Restaurant.objects.filter(status=Restaurant.Status.PUBLISHED))),
        }
        counts = {k: sum(len(v) for v in g.cells.values()) for k, g in grids.items()}

        dests = Destination.objects.filter(is_active=True).order_by("district", "name")
        total = dests.count()
        routable = 0
        covered = {c: {r: 0 for r in RADII} for c in grids}
        per_district = defaultdict(lambda: {"n": 0, **{c: 0 for c in grids}})
        gaps = []

        for d in dests.iterator():
            dist = d.district or "(unknown)"
            per_district[dist]["n"] += 1
            if d.latitude is None or d.longitude is None:
                gaps.append({"district": dist, "destination": d.name, "missing": "coordinates (no route possible)"})
                continue
            routable += 1
            missing_here = []
            for cat, grid in grids.items():
                name, km = grid.nearest(d.latitude, d.longitude)
                if km is not None:
                    for r in RADII:
                        if km <= r:
                            covered[cat][r] += 1
                    if km <= radius:
                        per_district[dist][cat] += 1
                    else:
                        missing_here.append(f"{cat} (nearest {km:.0f} km)")
                else:
                    missing_here.append(f"{cat} (none in DB)")
            if missing_here:
                gaps.append({"district": dist, "destination": d.name, "missing": "; ".join(missing_here)})

        summary = {
            "destinations": total,
            "routable": routable,
            "routable_pct": round(100 * routable / total, 1) if total else 0,
            "service_counts": counts,
            "coverage": {
                cat: {f"within_{r}km": covered[cat][r] for r in RADII}
                | {f"within_{r}km_pct": round(100 * covered[cat][r] / total, 1) if total else 0 for r in RADII}
                for cat in grids
            },
            "districts_missing_any_at_50km": {
                dist: {c: v["n"] - v[c] for c in grids if v["n"] - v[c] > 0}
                for dist, v in sorted(per_district.items())
                if any(v["n"] - v[c] > 0 for c in grids)
            },
            "destinations_with_gaps": len(gaps),
        }

        os.makedirs("reports", exist_ok=True)
        with open("reports/service_coverage.json", "w") as f:
            json.dump({"summary": summary, "gaps": gaps}, f, indent=1)
        with open("reports/service_coverage_gaps.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["district", "destination", "missing"])
            w.writeheader()
            w.writerows(gaps)

        self.stdout.write(json.dumps(summary["coverage"] | {
            "destinations": total, "routable": routable,
            "destinations_with_gaps": len(gaps)}, indent=1))
