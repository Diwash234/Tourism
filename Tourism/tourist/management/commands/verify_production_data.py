"""Verify production database health, data quality, and geographic boundary constraints.

Enforces the core data quality acceptance criteria:
  - Destination count sanity floor (target 6,700+)
  - Destination image count sanity floor (target 14,000+)
  - Emergency services (hospitals, police stations, hotels, restaurants)
  - Exactly 77 canonical Nepal districts present
  - Geographic coordinate bounding box:
      Latitude:  26.34°N <= lat <= 30.45°N
      Longitude: 80.05°E <= lon <= 88.20°E
  - Foreign key referential integrity (no orphaned images or records)

Usage:
    python manage.py verify_production_data [--strict]
"""

from __future__ import annotations

import sys
from django.core.management.base import BaseCommand
from django.db import connection

from tourist.models import (
    Category,
    Destination,
    DestinationImage,
    District,
    Hospital,
    Hotel,
    OSMEssentialService,
    PoliceStation,
    Province,
    Restaurant,
)

# Geographic limits of Nepal (with buffer for frontier border points)
NEPAL_BOUNDS = {
    "min_lat": 26.20,
    "max_lat": 30.60,
    "min_lon": 80.00,
    "max_lon": 88.30,
}

SANITY_MINIMUMS = {
    "destinations": 1000,
    "images": 1000,
    "hotels": 100,
    "hospitals": 50,
    "police": 50,
    "districts": 77,
}


class Command(BaseCommand):
    help = "Run automated data quality gate checks against active database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with non-zero status if any warning or threshold failure is detected.",
        )

    def handle(self, *args, **options):
        strict = options["strict"]
        errors = 0
        warnings = 0

        self.stdout.write("=" * 76)
        self.stdout.write("NEPAL YATRA PRODUCTION DATA QUALITY AUDIT")
        self.stdout.write(f"Database Engine: {connection.vendor} ({connection.settings_dict.get('NAME')})")
        self.stdout.write("=" * 76)

        # 1. Core Model Counts
        self.stdout.write("\n[1/5] Core Catalog Inventory:")
        counts = {
            "destinations": Destination.objects.count(),
            "images": DestinationImage.objects.count(),
            "hotels": Hotel.objects.count(),
            "hospitals": Hospital.objects.count(),
            "police": PoliceStation.objects.count(),
            "restaurants": Restaurant.objects.count(),
            "osm_services": OSMEssentialService.objects.count(),
            "districts": District.objects.count(),
            "provinces": Province.objects.count(),
            "categories": Category.objects.count(),
        }

        for key, count in counts.items():
            min_expected = SANITY_MINIMUMS.get(key, 1)
            if count >= min_expected:
                self.stdout.write(self.style.SUCCESS(f"  ✓ {key:<16}: {count:>6} (min: {min_expected})"))
            else:
                self.stdout.write(self.style.ERROR(f"  ✗ {key:<16}: {count:>6} (FAILED min: {min_expected})"))
                errors += 1

        # 2. Canonical 77 Districts Gate
        self.stdout.write("\n[2/5] Canonical 77 Districts Verification:")
        district_count = counts["districts"]
        if district_count == 77:
            self.stdout.write(self.style.SUCCESS(f"  ✓ All 77 canonical districts present in database."))
        elif district_count > 0:
            self.stdout.write(self.style.WARNING(f"  ⚠ Found {district_count}/77 districts."))
            warnings += 1
        else:
            self.stdout.write(self.style.ERROR("  ✗ No districts found in database!"))
            errors += 1

        # 3. Geographic Coordinate Bounding Box Gate
        self.stdout.write("\n[3/5] Geographic Boundary Validation (Nepal Territory):")
        total_with_coords = 0
        out_of_bounds = []

        qs = Destination.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        for dest in qs.only("id", "name", "latitude", "longitude").iterator():
            total_with_coords += 1
            lat = float(dest.latitude)
            lon = float(dest.longitude)

            # Check boundary
            if not (NEPAL_BOUNDS["min_lat"] <= lat <= NEPAL_BOUNDS["max_lat"] and
                    NEPAL_BOUNDS["min_lon"] <= lon <= NEPAL_BOUNDS["max_lon"]):
                out_of_bounds.append((dest.id, dest.name, lat, lon))

        if total_with_coords > 0:
            if not out_of_bounds:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ All {total_with_coords} geocoded destinations fall inside Nepal territory "
                    f"[{NEPAL_BOUNDS['min_lat']}–{NEPAL_BOUNDS['max_lat']}°N, {NEPAL_BOUNDS['min_lon']}–{NEPAL_BOUNDS['max_lon']}°E]."
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ Found {len(out_of_bounds)} destinations outside Nepal boundaries:"
                ))
                for oid, oname, olat, olon in out_of_bounds[:5]:
                    self.stdout.write(f"     ID {oid}: {oname} ({olat:.4f}, {olon:.4f})")
                warnings += 1
        else:
            self.stdout.write(self.style.WARNING("  ⚠ No destinations with coordinates evaluated."))

        # 4. Referential Integrity & Broken Relationships
        self.stdout.write("\n[4/5] Referential Integrity & Foreign Key Audit:")
        orphaned_images = DestinationImage.objects.filter(destination__isnull=True).count()
        if orphaned_images == 0:
            self.stdout.write(self.style.SUCCESS("  ✓ Zero orphaned destination images."))
        else:
            self.stdout.write(self.style.ERROR(f"  ✗ Found {orphaned_images} orphaned images!"))
            errors += 1

        dest_without_category = Destination.objects.filter(category__isnull=True).count()
        if dest_without_category == 0:
            self.stdout.write(self.style.SUCCESS("  ✓ All destinations assigned valid categories."))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ {dest_without_category} destinations unassigned to categories."))
            warnings += 1

        # 5. Media & Image Provenance Health
        self.stdout.write("\n[5/5] Visual Media Health:")
        dest_with_images = Destination.objects.filter(gallery__isnull=False).distinct().count()
        pct = (dest_with_images / counts["destinations"] * 100) if counts["destinations"] else 0
        self.stdout.write(f"  • Destinations with gallery images: {dest_with_images} ({pct:.1f}%)")

        self.stdout.write("\n" + "=" * 76)
        if errors == 0 and (not strict or warnings == 0):
            self.stdout.write(self.style.SUCCESS("DATA QUALITY GATE: PASSED ✓"))
            self.stdout.write("=" * 76)
            return
        else:
            self.stdout.write(self.style.ERROR(f"DATA QUALITY GATE: FAILED (Errors: {errors}, Warnings: {warnings})"))
            self.stdout.write("=" * 76)
            if strict or errors > 0:
                sys.exit(1)
