"""Audit and mark approximate/centroid coordinates for facilities.

Identifies hospitals, police stations, and hotels that share coordinates with
parent destination centroids or cluster at identical city coordinates (e.g. 28
hospitals at Biratnagar), marking them as APPROXIMATE so nearby queries do not
present them with false 0-meter precision.
"""
from __future__ import annotations

from collections import Counter
from django.core.management.base import BaseCommand
from tourist.models import Destination, Hospital, PoliceStation, Hotel


class Command(BaseCommand):
    help = "Audit and mark approximate coordinates on hospitals, police stations, and hotels."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without modifying records.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        dest_coords = {
            (round(float(d.latitude), 5), round(float(d.longitude), 5))
            for d in Destination.objects.filter(latitude__isnull=False, longitude__isnull=False)
        }

        # Cluster detection
        h_coords = Counter(
            (round(float(h.latitude), 5), round(float(h.longitude), 5))
            for h in Hospital.objects.filter(latitude__isnull=False, longitude__isnull=False)
        )
        p_coords = Counter(
            (round(float(p.latitude), 5), round(float(p.longitude), 5))
            for p in PoliceStation.objects.filter(latitude__isnull=False, longitude__isnull=False)
        )
        hot_coords = Counter(
            (round(float(h.latitude), 5), round(float(h.longitude), 5))
            for h in Hotel.objects.filter(latitude__isnull=False, longitude__isnull=False)
        )

        h_marked, p_marked, hot_marked = 0, 0, 0

        for h in Hospital.objects.all().iterator():
            if h.latitude is None or h.longitude is None:
                continue
            pt = (round(float(h.latitude), 5), round(float(h.longitude), 5))
            is_parent_match = (
                h.destination and h.destination.latitude is not None and
                round(float(h.latitude), 5) == round(float(h.destination.latitude), 5) and
                round(float(h.longitude), 5) == round(float(h.destination.longitude), 5)
            )
            is_approx = is_parent_match or pt in dest_coords or h_coords[pt] >= 3
            status = "APPROXIMATE" if is_approx else "EXACT"
            source = "destination_centroid" if is_approx else (h.coordinate_source or "sourced_listing")
            if h.coordinate_status != status:
                h_marked += 1
                if not dry_run:
                    h.coordinate_status = status
                    h.coordinate_source = source
                    h.save(update_fields=["coordinate_status", "coordinate_source"])

        for p in PoliceStation.objects.all().iterator():
            if p.latitude is None or p.longitude is None:
                continue
            pt = (round(float(p.latitude), 5), round(float(p.longitude), 5))
            is_parent_match = (
                p.destination and p.destination.latitude is not None and
                round(float(p.latitude), 5) == round(float(p.destination.latitude), 5) and
                round(float(p.longitude), 5) == round(float(p.destination.longitude), 5)
            )
            is_approx = is_parent_match or pt in dest_coords or p_coords[pt] >= 3
            status = "APPROXIMATE" if is_approx else "EXACT"
            source = "destination_centroid" if is_approx else (p.coordinate_source or "sourced_listing")
            if p.coordinate_status != status:
                p_marked += 1
                if not dry_run:
                    p.coordinate_status = status
                    p.coordinate_source = source
                    p.save(update_fields=["coordinate_status", "coordinate_source"])

        for hot in Hotel.objects.all().iterator():
            if hot.latitude is None or hot.longitude is None:
                continue
            pt = (round(float(hot.latitude), 5), round(float(hot.longitude), 5))
            is_parent_match = (
                hot.destination and hot.destination.latitude is not None and
                round(float(hot.latitude), 5) == round(float(hot.destination.latitude), 5) and
                round(float(hot.longitude), 5) == round(float(hot.destination.longitude), 5)
            )
            is_approx = is_parent_match or pt in dest_coords or hot_coords[pt] >= 3
            status = "APPROXIMATE" if is_approx else "EXACT"
            source = "destination_centroid" if is_approx else (hot.coordinate_source or "sourced_listing")
            if hot.coordinate_status != status:
                hot_marked += 1
                if not dry_run:
                    hot.coordinate_status = status
                    hot.coordinate_source = source
                    hot.save(update_fields=["coordinate_status", "coordinate_source"])

        msg = (
            f"Coordinate audit complete: hospitals_updated={h_marked}, "
            f"police_updated={p_marked}, hotels_updated={hot_marked}"
        )
        if dry_run:
            msg += " (DRY RUN)"
        self.stdout.write(self.style.SUCCESS(msg))
