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

    def handle(self, *args, **opts):
        from navigation.route_engine import cached_route

        dests = (Destination.objects.filter(is_active=True)
                 .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
                 .order_by("id"))
        if opts["sample"]:
            dests = dests[: opts["sample"]]

        origins = {"source_city_kathmandu": KATHMANDU, "user_gps_current_location": USER_GPS}
        stats = {k: {"ok": 0, "failed": 0, "sources": {}, "ratios": []} for k in origins}
        failures = []

        for i, d in enumerate(dests.iterator(), 1):
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
            if i % 500 == 0:
                self.stdout.write(f"  [{i}] kathmandu ok={stats['source_city_kathmandu']['ok']} "
                                  f"gps ok={stats['user_gps_current_location']['ok']}")

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
        with open("reports/route_audit.json", "w") as f:
            json.dump({"summary": summary, "failure_count": len(failures),
                       "failures_sample": failures[:50]}, f, indent=1)
        with open("reports/route_audit_failures.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["origin", "destination", "district", "error"])
            w.writeheader()
            w.writerows(failures)

        self.stdout.write(self.style.SUCCESS(json.dumps(summary, indent=1)))
        self.stdout.write(f"failures: {len(failures)} (see reports/route_audit_failures.csv)")
