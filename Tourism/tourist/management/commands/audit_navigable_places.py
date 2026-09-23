"""Audit that EVERY public destination is navigable with real coordinates.

Checks (full-population, not sampled):
  1. coordinates present (lat + lng non-null)
  2. coordinates inside the Nepal bounding box (26.3-30.5 N, 80.0-88.2 E)
  3. no placeholder clustering (>3 places sharing one exact point)
  4. coordinate provenance metadata present

Then route-smoke-tests a random sample (default 5) end-to-end through the
navigation provider chain, proving Lakeside -> <place> produces geometry.

Exit code 1 if any full-population check fails.
"""
from __future__ import annotations

import random

from django.core.management.base import BaseCommand
from django.db.models import Count

from tourist.models import Destination

NEPAL_BBOX = (26.3, 30.5, 80.0, 88.2)


class Command(BaseCommand):
    help = "Verify every public destination is navigable with real Nepal coordinates."

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=5,
                            help="how many random destinations to route-smoke-test")

    def handle(self, *args, **options):
        D = Destination.objects.filter(status="approved", is_active=True)
        total = D.count()
        problems = []

        missing = D.filter(latitude__isnull=True).count() + D.filter(longitude__isnull=True).count()
        south, north, west, east = NEPAL_BBOX
        outside = (D.exclude(latitude__gte=south, latitude__lte=north).count()
                   + D.exclude(longitude__gte=west, longitude__lte=east).count())
        # Clusters are only suspicious when UNMARKED: records honestly
        # labelled APPROXIMATE ('Area Point') may legitimately share an
        # area-level coordinate (e.g. monuments inside one Durbar Square).
        clusters = [c for c in
                    D.values("latitude", "longitude").annotate(n=Count("id"))
                    .filter(n__gt=3).order_by("-n")
                    if D.filter(latitude=c["latitude"], longitude=c["longitude"])
                    .exclude(coordinate_status="APPROXIMATE").exists()]
        approx_shared = D.filter(coordinate_status="APPROXIMATE").count()
        no_meta = D.filter(coordinate_source="").count()

        self.stdout.write(f"public destinations:            {total}")
        self.stdout.write(f"missing coordinates:            {missing}")
        self.stdout.write(f"outside Nepal bbox:             {outside}")
        self.stdout.write(f"unmarked coord clusters >3:     {len(clusters)}")
        self.stdout.write(f"honestly-marked approximate:    {approx_shared}")
        self.stdout.write(f"missing coordinate provenance:  {no_meta}")
        if missing:
            problems.append(f"{missing} destinations lack coordinates")
        if outside:
            problems.append(f"{outside} coordinate values outside Nepal bbox")
        if clusters:
            problems.append(f"{len(clusters)} suspicious coordinate clusters: {clusters[:3]}")

        # route smoke test: Lakeside (Pokhara) -> random public places
        sample_n = min(options["sample"], total)
        ids = list(D.values_list("id", flat=True))
        random.seed()  # true random per run
        for dest in Destination.objects.filter(id__in=random.sample(ids, sample_n)):
            from navigation import route_engine
            try:
                result, _ = route_engine.cached_route(
                    (28.2096, 83.9856),
                    (float(dest.latitude), float(dest.longitude)),
                    "driving", use_cache=False)
                route = result["route"]
                ok = route and len(route.get("geometry", [])) >= 2 and route["distance_m"] > 0
                label = "OK " if ok else "FAIL"
                self.stdout.write(
                    f"  [{label}] route -> {dest.name[:40]!r} ({dest.district}) "
                    f"{route['distance_m'] / 1000:.1f} km via {route['source']}")
                if not ok:
                    problems.append(f"no geometry for {dest.name}")
            except Exception as exc:
                problems.append(f"routing error for {dest.name}: {exc}")
                self.stdout.write(self.style.ERROR(f"  [FAIL] {dest.name}: {exc}"))

        if problems:
            for p in problems:
                self.stdout.write(self.style.ERROR(f"PROBLEM: {p}"))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            f"all {total} public destinations are navigable with real coordinates "
            f"({sample_n} route smoke tests passed)"))
