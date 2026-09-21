"""
audit_routes — prove navigation works for EVERY destination (owner request:
"real routes for every destination of 6659 from current location or the
source to destination").

For all active destinations with coordinates it computes routes through the
SAME central engine the public API uses (navigation.route_engine.cached_route
— OSRM when configured, labelled corridor-graph fallback otherwise; no
per-view geometry invention), from two kinds of source:

  * a named source city  — Kathmandu centre (27.7172, 85.3240);
  * a raw "current location" GPS point — Pokhara Lakeside (28.2096, 83.9856),
    proving unnamed user-GPS origins work exactly like city origins.

For every route it records the honest source label (osrm / graphml_fallback /
straight_line_fallback) and the route-vs-straight-line ratio, so inflated or
fabricated geometry would show up. Rate limiting only applies to HTTP
requests; this audit calls the engine directly (request=None), which is the
identical code path minus throttling.

Writes reports/route_audit.json (+ route_audit_failures.csv).

Usage:  python manage.py audit_routes [--sample N]
"""

import csv
import json
import math
import os
import statistics

from django.core.management.base import BaseCommand

from tourist.models import Destination

KATHMANDU = (27.7172, 85.3240)   # named source city
USER_GPS = (28.2096, 83.9856)    # raw "current location" (Pokhara Lakeside)

# "Current location" can be ANYWHERE — this grid proves it: raw GPS points
# spread across Terai / hills / high Himalaya / remote west / border edges.
GPS_GRID = {
    "gps_bhimdatta_far_west_terai": (28.8372, 80.1838),
    "gps_dhangadhi_west_terai": (28.7000, 80.6000),
    "gps_birgunj_central_terai": (27.0000, 84.8750),
    "gps_biratnagar_east_terai": (26.4567, 87.2718),
    "gps_gorkha_mid_hills": (28.0000, 84.6300),
    "gps_phungling_east_hills": (27.3500, 87.7000),
    "gps_namche_high_himalaya": (27.8025, 86.7106),
    "gps_gamgadhi_remote_northwest": (29.4167, 82.0167),
    "gps_rasuwagadhi_north_border": (28.2506, 85.3771),
    "gps_manang_trans_himalaya": (28.6667, 84.0167),
}


def _hav(a, b):
    R = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


class Command(BaseCommand):
    help = "Route audit: every destination from a source city and from raw user GPS."

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=0,
                            help="audit only the first N destinations (0 = all)")
        parser.add_argument("--gps-grid", action="store_true",
                            help="route from 10 raw 'current location' GPS points spread "
                                 "across Terai/hills/Himalaya/remote west/border instead of "
                                 "the default city+GPS pair")
        parser.add_argument("--per-district", type=int, default=0,
                            help="stratified sample: audit up to N destinations per district "
                                 "(evenly spaced by id); 0 = no stratification")

    def _stratified(self, qs, per_district):
        from collections import defaultdict
        by_district = defaultdict(list)
        for d in qs:
            by_district[d.district or ""].append(d)
        picked = []
        for district in sorted(by_district):
            rows = by_district[district]
            if len(rows) <= per_district:
                picked.extend(rows)
            else:
                step = len(rows) / per_district
                picked.extend(rows[int(i * step)] for i in range(per_district))
        picked.sort(key=lambda d: d.id)
        return picked

    def handle(self, *args, **opts):
        from navigation.route_engine import cached_route

        qs = (Destination.objects.filter(is_active=True)
              .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
              .order_by("id"))
        if opts["per_district"]:
            dests = self._stratified(qs, opts["per_district"])
        elif opts["sample"]:
            dests = qs[: opts["sample"]]
        else:
            dests = qs

        if opts["gps_grid"]:
            origins = GPS_GRID
            out_json, out_csv = "reports/route_audit_multi_gps.json", "reports/route_audit_multi_gps_failures.csv"
        else:
            origins = {"source_city_kathmandu": KATHMANDU, "user_gps_current_location": USER_GPS}
            out_json, out_csv = "reports/route_audit.json", "reports/route_audit_failures.csv"
        stats = {k: {"ok": 0, "failed": 0, "sources": {}, "ratios": []} for k in origins}
        failures = []

        it = dests.iterator() if hasattr(dests, "iterator") else dests
        for i, d in enumerate(it, 1):
            target = (float(d.latitude), float(d.longitude))
            for label, origin in origins.items():
                st = stats[label]
                try:
                    result, _cached = cached_route(origin, target, "driving", request=None)
                    route = result["route"]
                    src = route.get("source", "unknown")
                    km = float(route["distance_m"]) / 1000.0
                    st["ok"] += 1
                    st["sources"][src] = st["sources"].get(src, 0) + 1
                    straight = _hav(origin, target)
                    if straight > 1:
                        st["ratios"].append(km / straight)
                except Exception as exc:
                    st["failed"] += 1
                    failures.append({"origin": label, "destination": d.name,
                                     "district": d.district or "", "error": str(exc)[:200]})
            if i % 100 == 0:
                totals = " ".join(f"{k.replace('gps_', '').replace('_fallback', '')}:{v['ok']}"
                                  for k, v in list(stats.items())[:3])
                failed = sum(v["failed"] for v in stats.values())
                self.stdout.write(f"  [{i}/{len(dests) if isinstance(dests, list) else '?'}] {totals} ... failed={failed}")

        summary = {}
        for label, st in stats.items():
            ratios = st["ratios"]
            summary[label] = {
                "ok": st["ok"], "failed": st["failed"],
                "sources": st["sources"],
                "median_route_over_straight": round(statistics.median(ratios), 2) if ratios else None,
                "p95_route_over_straight": round(sorted(ratios)[int(len(ratios) * 0.95)], 2) if ratios else None,
            }

        os.makedirs("reports", exist_ok=True)
        with open(out_json, "w") as f:
            json.dump({"summary": summary, "failure_count": len(failures),
                       "failures_sample": failures[:50]}, f, indent=1)
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["origin", "destination", "district", "error"])
            w.writeheader()
            w.writerows(failures)

        self.stdout.write(self.style.SUCCESS(json.dumps(summary, indent=1)))
        self.stdout.write(f"failures: {len(failures)} (see {out_csv})")
