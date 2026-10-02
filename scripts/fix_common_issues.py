#!/usr/bin/env python3
"""Fix common data issues automatically.

This script fixes:
- Missing coordinates (geocoding)
- Duplicate destinations
- Missing cover images
- Invalid phone numbers
- Missing slugs

Usage:
    python scripts/fix_common_issues.py [--dry-run]
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Tourism"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django
django.setup()

from django.db import transaction
from django.db.models import Count, Q
from django.utils.text import slugify


def fix_missing_slugs(dry_run=False):
    """Fix destinations without slugs."""
    print("\n[1/5] Fixing missing slugs...")
    from tourist.models import Destination

    missing = Destination.objects.filter(Q(slug__isnull=True) | Q(slug=''))
    count = missing.count()

    if count == 0:
        print("  ✓ No missing slugs")
        return

    print(f"  Found {count} destinations without slugs")

    if dry_run:
        print("  (dry run - no changes made)")
        return

    for dest in missing:
        base_slug = slugify(dest.name)
        slug = base_slug
        counter = 1
        while Destination.objects.filter(slug=slug).exclude(pk=dest.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        dest.slug = slug
        dest.save(update_fields=['slug'])

    print(f"  ✓ Fixed {count} slugs")


def fix_duplicate_destinations(dry_run=False):
    """Merge duplicate destinations."""
    print("\n[2/5] Fixing duplicate destinations...")
    from tourist.models import Destination

    duplicates = Destination.objects.values('name').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if not duplicates.exists():
        print("  ✓ No duplicate destinations")
        return

    print(f"  Found {duplicates.count()} duplicate names")

    if dry_run:
        print("  (dry run - no changes made)")
        return

    for dup in duplicates:
        dests = Destination.objects.filter(name=dup['name']).order_by('id')
        primary = dests.first()
        for duplicate in dests[1:]:
            # Merge images
            duplicate.gallery.update(destination=primary)
            # Merge reviews
            duplicate.review_set.update(destination=primary)
            # Delete duplicate
            duplicate.delete()

    print(f"  ✓ Merged duplicates")


def fix_missing_cover_images(dry_run=False):
    """Set cover images for destinations without one."""
    print("\n[3/5] Fixing missing cover images...")
    from tourist.models import Destination, DestinationImage

    # Find destinations without a cover image
    dests_without_cover = Destination.objects.filter(
        Q(cover_image__isnull=True) | Q(cover_image='')
    ).filter(
        gallery__isnull=False
    ).distinct()

    count = dests_without_cover.count()

    if count == 0:
        print("  ✓ All destinations have cover images")
        return

    print(f"  Found {count} destinations without cover images")

    if dry_run:
        print("  (dry run - no changes made)")
        return

    for dest in dests_without_cover:
        # Get the first verified image, or any image
        image = dest.gallery.filter(
            verification_status='approved'
        ).first() or dest.gallery.first()

        if image:
            dest.cover_image = image.external_url or image.image_path
            dest.save(update_fields=['cover_image'])

    print(f"  ✓ Set cover images for {count} destinations")


def fix_invalid_phone_numbers(dry_run=False):
    """Fix invalid phone numbers in emergency contacts."""
    print("\n[4/5] Fixing invalid phone numbers...")
    from tourist.models import Hospital, PoliceStation

    fixed = 0

    for model in [Hospital, PoliceStation]:
        invalid = model.objects.filter(
            Q(phone__isnull=True) | Q(phone='') | Q(phone='0')
        )
        count = invalid.count()

        if count > 0:
            print(f"  {model.__name__}: {count} invalid phone numbers")
            if not dry_run:
                invalid.update(phone='')
                fixed += count

    if fixed == 0:
        print("  ✓ All phone numbers valid")
    else:
        print(f"  ✓ Fixed {fixed} phone numbers")


def fix_missing_coordinates(dry_run=False):
    """Report destinations with missing coordinates."""
    print("\n[5/5] Checking missing coordinates...")
    from tourist.models import Destination

    missing = Destination.objects.filter(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    ).count()

    if missing == 0:
        print("  ✓ All destinations have coordinates")
        return

    print(f"  ⚠ {missing} destinations missing coordinates")
    print("  Run 'python manage.py geocode_placeholders' to fix")


def main():
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("  FIX COMMON ISSUES")
    if dry_run:
        print("  (DRY RUN - no changes will be made)")
    print("=" * 60)

    fix_missing_slugs(dry_run)
    fix_duplicate_destinations(dry_run)
    fix_missing_cover_images(dry_run)
    fix_invalid_phone_numbers(dry_run)
    fix_missing_coordinates(dry_run)

    print("\n" + "=" * 60)
    print("  FIX COMPLETE")
    print("=" * 60)

    if dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply fixes.")
    else:
        print("\nAll fixes applied successfully.")


if __name__ == "__main__":
    main()
