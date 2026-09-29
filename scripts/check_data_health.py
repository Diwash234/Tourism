#!/usr/bin/env python3
"""Check data health and integrity.

This script checks for:
- Missing images
- Broken foreign keys
- Duplicate entries
- Invalid coordinates
- Missing required fields

Usage:
    python scripts/check_data_health.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Tourism"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django
django.setup()

from django.db import connection
from django.db.models import Count, Q


def check_table_counts():
    """Check row counts for all major tables."""
    print("\n[1/6] Table Counts:")
    tables = [
        ("tourist_destination", "Destinations"),
        ("tourist_destinationimage", "Images"),
        ("tourist_hotel", "Hotels"),
        ("tourist_hospital", "Hospitals"),
        ("tourist_policestation", "Police Stations"),
        ("tourist_restaurant", "Restaurants"),
        ("tourist_osmessentialservice", "OSM Services"),
        ("tourist_managedpage", "CMS Pages"),
        ("tourist_contentsection", "CMS Sections"),
        ("tourist_user", "Users"),
        ("tourist_review", "Reviews"),
        ("tourist_booking", "Bookings"),
    ]

    for table, label in tables:
        try:
            with connection.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                status = "✓" if count > 0 else "⚠"
                print(f"  {status} {label}: {count}")
        except Exception as exc:
            print(f"  ✗ {label}: ERROR - {exc}")


def check_missing_images():
    """Check for destinations without images."""
    print("\n[2/6] Missing Images:")
    from tourist.models import Destination, DestinationImage

    total = Destination.objects.count()
    with_images = Destination.objects.filter(gallery__isnull=False).distinct().count()
    without_images = total - with_images

    print(f"  Total destinations: {total}")
    print(f"  With images: {with_images}")
    print(f"  Without images: {without_images}")

    if without_images > 0:
        pct = (without_images / total) * 100 if total > 0 else 0
        print(f"  ⚠ {pct:.1f}% of destinations have no images")


def check_invalid_coordinates():
    """Check for destinations with invalid coordinates."""
    print("\n[3/6] Invalid Coordinates:")
    from tourist.models import Destination

    # Nepal bounding box
    NEPAL_LAT_MIN, NEPAL_LAT_MAX = 26.0, 31.0
    NEPAL_LON_MIN, NEPAL_LON_MAX = 80.0, 89.0

    invalid = Destination.objects.filter(
        Q(latitude__isnull=True) |
        Q(longitude__isnull=True) |
        Q(latitude__lt=NEPAL_LAT_MIN) |
        Q(latitude__gt=NEPAL_LAT_MAX) |
        Q(longitude__lt=NEPAL_LON_MIN) |
        Q(longitude__gt=NEPAL_LON_MAX)
    ).count()

    null_island = Destination.objects.filter(latitude=0, longitude=0).count()

    print(f"  Invalid coordinates: {invalid}")
    print(f"  Null island (0,0): {null_island}")

    if invalid > 0:
        print(f"  ⚠ {invalid} destinations have invalid coordinates")


def check_duplicate_slugs():
    """Check for duplicate slugs."""
    print("\n[4/6] Duplicate Slugs:")
    from tourist.models import Destination

    duplicates = Destination.objects.values('slug').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if duplicates.exists():
        print(f"  ✗ Found {duplicates.count()} duplicate slugs:")
        for dup in duplicates[:5]:
            print(f"    - {dup['slug']}: {dup['count']} occurrences")
    else:
        print(f"  ✓ No duplicate slugs")


def check_orphaned_images():
    """Check for images without destinations."""
    print("\n[5/6] Orphaned Images:")
    from tourist.models import DestinationImage

    orphaned = DestinationImage.objects.filter(destination__isnull=True).count()
    print(f"  Orphaned images: {orphaned}")

    if orphaned > 0:
        print(f"  ⚠ {orphaned} images have no destination")


def check_cms_pages():
    """Check CMS page health."""
    print("\n[6/6] CMS Pages:")
    from tourist.models import ManagedPage, ContentSection

    total_pages = ManagedPage.objects.count()
    published = ManagedPage.objects.filter(status='published').count()
    draft = ManagedPage.objects.filter(status='draft').count()

    total_sections = ContentSection.objects.count()
    published_sections = ContentSection.objects.filter(status='published').count()

    print(f"  Pages: {total_pages} total, {published} published, {draft} draft")
    print(f"  Sections: {total_sections} total, {published_sections} published")

    if total_pages == 0:
        print(f"  ⚠ No CMS pages found")


def main():
    print("=" * 60)
    print("  DATA HEALTH CHECK")
    print("=" * 60)

    check_table_counts()
    check_missing_images()
    check_invalid_coordinates()
    check_duplicate_slugs()
    check_orphaned_images()
    check_cms_pages()

    print("\n" + "=" * 60)
    print("  CHECK COMPLETE")
    print("=" * 60)
    print("\nRecommendations:")
    print("  - Run 'python manage.py repair_real_place_images' to fix missing images")
    print("  - Run 'python manage.py merge_duplicate_destinations' to fix duplicates")
    print("  - Run 'python manage.py geocode_placeholders' to fix invalid coordinates")
    print()


if __name__ == "__main__":
    main()
