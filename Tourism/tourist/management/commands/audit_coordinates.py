"""
READ-ONLY coordinate quality audit.

Flags rows whose recorded coordinates are suspicious WITHOUT changing any
data (fixing coordinates needs a verified source — never guessed):

  1. Destinations whose coordinates sit >100 km from their own district's
     median point (clearly misplaced rows).
  2. Hospital / police rows sharing exact coordinates with another row of
     the same kind (same facility recorded twice under different names, or
     a centroid-level import).
  3. Hospital / police rows >25 km from their district's median point.

Usage (from Tourism/):
    python manage.py audit_coordinates                 # print summary
    python manage.py audit_coordinates --tsv out.tsv   # dump every flagged row
"""
import math
import re

from django.core.management.base import BaseCommand

from tourist.models import Destination, Hospital, PoliceStation


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _district_median(model, district_field="district"):
    """Per-district median lat/lon computed from that district's own rows —
    robust against a few bad rows skewing a mean."""
    by_district = {}
    for lat, lon, dist in model.objects.exclude(
        latitude=None
    ).exclude(longitude=None).values_list("latitude", "longitude", district_field):
        if not dist:
            continue
        by_district.setdefault(str(dist), []).append((float(lat), float(lon)))
    refs = {}
    for dist, pts in by_district.items():
        lat_med = sorted(p[0] for p in pts)[len(pts) // 2]
        lon_med = sorted(p[1] for p in pts)[len(pts) // 2]
        refs[dist] = (lat_med, lon_med)
    return refs


class Command(BaseCommand):
    help = "Read-only coordinate quality audit (flags suspicious rows, changes nothing)."

    def add_arguments(self, parser):
        parser.add_argument("--tsv", default=None,
                            help="Optional path to dump every flagged row as TSV.")

    def handle(self, *args, **options):
        flagged = []

        # --- 1. destinations far from their district median ----------------
        dest_refs = _district_median(Destination)
        n_dest_checked = 0
        for r in Destination.objects.exclude(latitude=None).exclude(
            longitude=None
        ).exclude(district=None).values(
            "id", "name", "slug", "district", "latitude", "longitude"
        ):
            ref = dest_refs.get(str(r["district"]))
            if not ref:
                continue
            n_dest_checked += 1
            d = _haversine_km(r["latitude"], r["longitude"], ref[0], ref[1])
            if d > 100:
                flagged.append((
                    "destination_far", r["id"], r["name"],
                    f'{round(d)} km from {r["district"]} median',
                    f'{float(r["latitude"]):.4f},{float(r["longitude"]):.4f}',
                    r["slug"],
                ))

        # --- 2 + 3. hospital / police directories --------------------------
        for label, model, dist_field in (
            ("hospital", Hospital, "district"),
            ("police", PoliceStation, "destination__district"),
        ):
            refs = _district_median(model, dist_field)
            seen_coords = {}
            n_checked = 0
            for r in model.objects.exclude(latitude=None).exclude(
                longitude=None
            ).values("id", "name", "latitude", "longitude", dist_field):
                n_checked += 1
                coord = (round(float(r["latitude"]), 4), round(float(r["longitude"]), 4))
                key = (label,) + coord
                if key in seen_coords:
                    flagged.append((
                        f"{label}_same_site", r["id"], r["name"],
                        f'shared coords with id {seen_coords[key]}',
                        f'{coord[0]},{coord[1]}', "",
                    ))
                else:
                    seen_coords[key] = r["id"]
                dist = r.get(dist_field)
                ref = refs.get(str(dist)) if dist else None
                if ref:
                    d = _haversine_km(r["latitude"], r["longitude"], ref[0], ref[1])
                    if d > 25:
                        flagged.append((
                            f"{label}_far", r["id"], r["name"],
                            f'{round(d)} km from {dist} median',
                            f'{float(r["latitude"]):.4f},{float(r["longitude"]):.4f}',
                            "",
                        ))
            self.stdout.write(
                f"{label:9} rows checked: {n_checked}"
            )
        self.stdout.write(f"destination rows checked: {n_dest_checked}")

        from collections import Counter
        by_kind = Counter(f[0] for f in flagged)
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(
            f"FLAGGED (no data was modified): {len(flagged)} rows"
        ))
        for kind, n in sorted(by_kind.items()):
            self.stdout.write(f"  {kind:28} {n}")

        if options.get("tsv"):
            with open(options["tsv"], "w", encoding="utf-8") as fh:
                fh.write("kind\tid\tname\tdetail\tlat,lon\tslug\n")
                for f in sorted(flagged):
                    fh.write("\t".join(str(x) for x in f) + "\n")
            self.stdout.write(f"TSV written to {options['tsv']}")

        self.stdout.write("")
        self.stdout.write(
            "Fixing coordinates requires a verified source per row (admin "
            "review or a trusted geocoder with provenance recorded in "
            "coordinate_source). This command intentionally changes nothing."
        )
