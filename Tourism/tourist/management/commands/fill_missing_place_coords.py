"""Propose (never silently publish) missing destination coordinates.

V6 §11 workflow: coordinates inferred from same-name twins or district
means are CANDIDATES — written to dataset/osm_reports/coordinate_
candidates.json with basis + confidence and approval_state=
pending_admin. Nothing is written to Destination.latitude/longitude
unless an operator explicitly passes --publish (an admin decision).
City fill from municipality / recorded neighbour stays automatic
(labelled metadata, not coordinates).
Also writes Tourism/dataset/destination_locations.json so clones can
re-apply the same recorded fields without committing db.sqlite3.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.location_sync import (
    apply_destination_locations,
    export_destination_locations,
    fill_city_from_records,
    fill_coords_from_records,
    fill_ktm_distance,
)
from tourist.models import Destination


class Command(BaseCommand):
    help = "Fill missing destination city/coordinates from other recorded places and export JSON."

    def add_arguments(self, parser):
        parser.add_argument("--no-export", action="store_true", help="Skip writing destination_locations.json")
        parser.add_argument("--no-apply", action="store_true", help="Skip applying destination_locations.json first")
        parser.add_argument("--publish", action="store_true",
                            help="Admin decision: write inferred coordinates to the DB "
                                 "(default: candidates JSON only, DB untouched)")
        parser.add_argument("--candidates-out",
                            default="dataset/osm_reports/coordinate_candidates.json")

    def handle(self, *args, **options):
        applied = 0
        if not options.get("no_apply"):
            applied = apply_destination_locations()
        filled_coords = 0
        filled_city = 0
        filled_distance = 0
        qs = Destination.objects.filter(is_active=True)

        import json
        from decimal import Decimal
        from pathlib import Path
        candidates = []
        for dest in (qs.filter(latitude__isnull=True) | qs.filter(longitude__isnull=True)).distinct():
            before = (dest.latitude, dest.longitude)
            if fill_coords_from_records(dest):
                basis = "same_name_twin" if Destination.objects.filter(
                    name__iexact=dest.name, latitude__isnull=False).exclude(pk=dest.pk).exists() \
                    else "district_or_city_mean"
                cand = {"id": dest.id, "name": dest.name, "district": dest.district,
                        "province": dest.province,
                        "candidate_latitude": float(dest.latitude),
                        "candidate_longitude": float(dest.longitude),
                        "basis": basis, "confidence": "low",
                        "approval_state": "pending_admin"}
                if options.get("publish"):
                    dest.save(update_fields=["latitude", "longitude", "updated_at"])
                    filled_coords += 1
                    cand["approval_state"] = "published_via_--publish"
                else:
                    # never persist inferred coordinates by default
                    dest.latitude, dest.longitude = before
                candidates.append(cand)
        out = Path(options.get("candidates_out"))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"policy": "inferred coordinates are candidates; "
                                              "admin approval required before publication",
                                   "candidates": candidates}, indent=1, ensure_ascii=False))

        for dest in (qs.filter(city__isnull=True) | qs.filter(city="")).distinct():
            if fill_city_from_records(dest):
                dest.save(update_fields=["city", "updated_at"])
                filled_city += 1

        refined_city = 0
        for dest in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            if fill_city_from_records(dest, upgrade=True):
                dest.save(update_fields=["city", "updated_at"])
                refined_city += 1

        for dest in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            if fill_ktm_distance(dest):
                dest.save(update_fields=["distance_from_kathmandu_km", "updated_at"])
                filled_distance += 1

        exported = 0
        if not options.get("no_export"):
            active_count = Destination.objects.filter(is_active=True).count()
            if active_count < 100:
                self.stdout.write("Skipping export: fewer than 100 destinations (likely a test database).")
            else:
                _, exported = export_destination_locations()

        remaining_coords = Destination.objects.filter(is_active=True, latitude__isnull=True).count()
        remaining_city = Destination.objects.filter(is_active=True).filter(
            Q(city__isnull=True) | Q(city="")
        ).count()
        self.stdout.write(self.style.SUCCESS(
            f"Applied JSON={applied}, filled coords={filled_coords}, city={filled_city}, "
            f"refined_city={refined_city}, ktm_distance={filled_distance}, exported={exported}. "
            f"Still missing coords={remaining_coords}, city={remaining_city}."
        ))
