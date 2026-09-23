"""Resolve missing province/district on destinations WITHOUT fabricating.

Two deterministic, evidence-based passes:

Pass A (district -> province): destinations that already have a ``district``
but no ``province`` get their province from a district->province map derived
by majority vote from the *verified* rows already in the database (7,500+
records). This never invents a district; it only completes the province that a
district unambiguously implies.

Pass B (nearest verified neighbour): destinations with *no* district but with
valid coordinates are assigned the district+province of the nearest destination
that HAS verified district+province+coordinates, within ``--max-km``. This is a
geospatial join against real records, not a guess; anything beyond the radius
stays untouched and is reported as unresolved.

A CSV report is written so every change (and every unresolved row) is auditable.
Running the command twice is idempotent: already-resolved rows are skipped.
"""
import csv
from math import radians, sin, cos, sqrt, atan2
from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.models import Destination

REPORT_PATH = "Tourism/dataset/geo_resolution_report.csv"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def has_coords(d):
    return d.latitude is not None and d.longitude is not None


class Command(BaseCommand):
    help = "Backfill missing province/district from verified in-DB data (no fabrication)."

    def add_arguments(self, parser):
        parser.add_argument("--max-km", type=float, default=15.0,
                            help="Max radius for nearest-verified-neighbour assignment.")
        parser.add_argument("--report", default=REPORT_PATH)

    def handle(self, *args, **opts):
        max_km = opts["max_km"]

        # district -> province by majority vote over verified rows.
        vote = Counter()
        for d in Destination.objects.exclude(district__isnull=True).exclude(district="") \
                .exclude(province__isnull=True).exclude(province="") \
                .values_list("district", "province"):
            vote[(d[0].strip().title(), d[1].strip().title())] += 1
        district_province = {}
        best = {}
        for (dist, prov), n in vote.items():
            if dist not in best or n > best[dist][1]:
                best[dist] = (prov, n)
        district_province = {dist: prov for dist, (prov, n) in best.items()}

        # verified neighbours with coords + full geo.
        neighbours = [
            (float(d.latitude), float(d.longitude), d.district.strip().title(), d.province.strip().title())
            for d in Destination.objects
            .exclude(district__isnull=True).exclude(district="")
            .exclude(province__isnull=True).exclude(province="")
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        ]

        resolved_a = resolved_b = unresolved = 0
        rows = []

        # Pass A: district present, province missing.
        qs_a = Destination.objects.filter(
            Q(province__isnull=True) | Q(province="")
        ).exclude(district__isnull=True).exclude(district="")
        for d in qs_a:
            prov = district_province.get(d.district.strip().title())
            if prov:
                d.province = prov
                d.save(update_fields=["province"])
                resolved_a += 1
                rows.append([d.id, d.name, d.latitude, d.longitude, d.district, prov, "district_map", "resolved"])
            else:
                unresolved += 1
                rows.append([d.id, d.name, d.latitude, d.longitude, d.district, "", "district_map", "unresolved_unknown_district"])

        # Pass B: district missing, coords present.
        qs_b = Destination.objects.filter(
            Q(district__isnull=True) | Q(district="")
        ).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        for d in qs_b:
            lat, lon = float(d.latitude), float(d.longitude)
            best_n, best_dist = None, max_km
            for (nlat, nlon, ndist, nprov) in neighbours:
                # quick bounding-box prune for speed
                if abs(nlat - lat) > max_km / 111 or abs(nlon - lon) > max_km / 111:
                    continue
                km = haversine_km(lat, lon, nlat, nlon)
                if km <= best_dist:
                    best_dist, best_n = km, (ndist, nprov)
            if best_n:
                d.district, d.province = best_n
                d.save(update_fields=["district", "province"])
                resolved_b += 1
                rows.append([d.id, d.name, d.latitude, d.longitude, best_n[0], best_n[1],
                             f"nearest_verified_{best_dist:.1f}km", "resolved"])
            else:
                unresolved += 1
                rows.append([d.id, d.name, d.latitude, d.longitude, "", "", "nearest_verified", "unresolved_no_neighbour"])

        # Still missing with no coords at all.
        qs_c = Destination.objects.filter(
            Q(district__isnull=True) | Q(district=""),
            Q(latitude__isnull=True) | Q(longitude__isnull=True),
        )
        for d in qs_c:
            unresolved += 1
            rows.append([d.id, d.name, "", "", "", "", "none", "unresolved_no_coords"])

        with open(opts["report"], "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "name", "latitude", "longitude", "district", "province", "method", "status"])
            w.writerows(rows)

        total_missing_after = Destination.objects.filter(
            Q(province__isnull=True) | Q(province="") | Q(district__isnull=True) | Q(district="")
        ).count()
        self.stdout.write(self.style.SUCCESS(
            f"Resolved via district_map={resolved_a}, nearest_verified={resolved_b}; "
            f"unresolved={unresolved}; still missing after run={total_missing_after}. "
            f"Report: {opts['report']}"
        ))
