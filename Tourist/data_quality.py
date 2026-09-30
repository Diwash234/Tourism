"""Data quality checker and reporter.

Provides:
- Data quality checks
- Consistency validation
- Anomaly detection
- Quality reports
- Auto-fix common issues
"""
import logging
from collections import defaultdict

from django.db import transaction
from django.db.models import Q, Count, Avg
from django.core.cache import cache

from .models import (
    Destination, DestinationImage, Hotel, Hospital, PoliceStation,
    Restaurant, Review, Rating, User, EmergencyContact,
)

logger = logging.getLogger(__name__)


def run_quality_checks():
    """Run all data quality checks.

    Returns:
        Dict with check results
    """
    results = {
        'missing_fields': check_missing_fields(),
        'invalid_coordinates': check_invalid_coordinates(),
        'orphaned_records': check_orphaned_records(),
        'duplicate_entries': check_duplicate_entries(),
        'inconsistent_data': check_inconsistent_data(),
        'missing_images': check_missing_images(),
    }

    # Calculate overall score
    total_issues = sum(len(v) for v in results.values())
    results['total_issues'] = total_issues
    results['quality_score'] = max(0, 100 - total_issues)

    return results


def generate_quality_report():
    """Generate a comprehensive data quality report.

    Returns:
        Dict with quality report
    """
    cache_key = "data_quality_report"
    cached = cache.get(cache_key)
    if cached:
        return cached

    checks = run_quality_checks()

    report = {
        'summary': {
            'total_destinations': Destination.objects.count(),
            'total_images': DestinationImage.objects.count(),
            'total_hotels': Hotel.objects.count(),
            'total_hospitals': Hospital.objects.count(),
            'total_police_stations': PoliceStation.objects.count(),
            'total_restaurants': Restaurant.objects.count(),
            'total_reviews': Review.objects.count(),
            'total_users': User.objects.count(),
        },
        'issues': checks,
        'recommendations': _generate_recommendations(checks),
    }

    # Cache for 1 hour
    cache.set(cache_key, report, 3600)

    return report


def fix_common_issues(dry_run=True):
    """Fix common data quality issues.

    Args:
        dry_run: If True, only report issues without fixing

    Returns:
        Dict with fix results
    """
    fixes = {
        'fixed': [],
        'skipped': [],
    }

    # Fix destinations without slugs
    for dest in Destination.objects.filter(Q(slug__isnull=True) | Q(slug='')):
        if dry_run:
            fixes['skipped'].append(f"Destination {dest.id} has no slug")
        else:
            from django.utils.text import slugify
            dest.slug = slugify(dest.name)
            dest.save(update_fields=['slug'])
            fixes['fixed'].append(f"Fixed slug for destination {dest.id}")

    # Fix images without destinations
    orphaned_images = DestinationImage.objects.filter(destination__isnull=True)
    if dry_run:
        fixes['skipped'].append(f"{orphaned_images.count()} orphaned images")
    else:
        orphaned_images.delete()
        fixes['fixed'].append(f"Deleted {orphaned_images.count()} orphaned images")

    # Fix invalid phone numbers
    for model in [Hospital, PoliceStation]:
        invalid = model.objects.filter(Q(phone__isnull=True) | Q(phone='') | Q(phone='nan'))
        if dry_run:
            fixes['skipped'].append(f"{invalid.count()} invalid phone numbers in {model.__name__}")
        else:
            invalid.update(phone='')
            fixes['fixed'].append(f"Fixed {invalid.count()} phone numbers in {model.__name__}")

    return fixes


def check_missing_fields():
    """Check for missing required fields.

    Returns:
        List of issues
    """
    issues = []

    # Destinations without names
    dests_without_name = Destination.objects.filter(Q(name__isnull=True) | Q(name=''))
    if dests_without_name.exists():
        issues.append({
            'type': 'missing_name',
            'count': dests_without_name.count(),
            'model': 'Destination',
        })

    # Destinations without coordinates
    dests_without_coords = Destination.objects.filter(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    )
    if dests_without_coords.exists():
        issues.append({
            'type': 'missing_coordinates',
            'count': dests_without_coords.count(),
            'model': 'Destination',
        })

    # Hotels without names
    hotels_without_name = Hotel.objects.filter(Q(name__isnull=True) | Q(name=''))
    if hotels_without_name.exists():
        issues.append({
            'type': 'missing_name',
            'count': hotels_without_name.count(),
            'model': 'Hotel',
        })

    return issues


def check_invalid_coordinates():
    """Check for invalid coordinates.

    Returns:
        List of issues
    """
    issues = []

    # Nepal bounding box
    NEPAL_LAT_MIN, NEPAL_LAT_MAX = 26.0, 31.0
    NEPAL_LON_MIN, NEPAL_LON_MAX = 80.0, 89.0

    invalid_coords = Destination.objects.filter(
        Q(latitude__lt=NEPAL_LAT_MIN) |
        Q(latitude__gt=NEPAL_LAT_MAX) |
        Q(longitude__lt=NEPAL_LON_MIN) |
        Q(longitude__gt=NEPAL_LON_MAX)
    )

    if invalid_coords.exists():
        issues.append({
            'type': 'invalid_coordinates',
            'count': invalid_coords.count(),
            'model': 'Destination',
        })

    # Null island
    null_island = Destination.objects.filter(latitude=0, longitude=0)
    if null_island.exists():
        issues.append({
            'type': 'null_island',
            'count': null_island.count(),
            'model': 'Destination',
        })

    return issues


def check_orphaned_records():
    """Check for orphaned records.

    Returns:
        List of issues
    """
    issues = []

    # Images without destinations
    orphaned_images = DestinationImage.objects.filter(destination__isnull=True)
    if orphaned_images.exists():
        issues.append({
            'type': 'orphaned_images',
            'count': orphaned_images.count(),
        })

    # Hotels without destinations
    orphaned_hotels = Hotel.objects.filter(destination__isnull=True)
    if orphaned_hotels.exists():
        issues.append({
            'type': 'orphaned_hotels',
            'count': orphaned_hotels.count(),
        })

    return issues


def check_duplicate_entries():
    """Check for duplicate entries.

    Returns:
        List of issues
    """
    issues = []

    # Duplicate destination names
    dup_names = Destination.objects.values('name').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if dup_names.exists():
        issues.append({
            'type': 'duplicate_names',
            'count': dup_names.count(),
            'model': 'Destination',
        })

    # Duplicate slugs
    dup_slugs = Destination.objects.values('slug').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if dup_slugs.exists():
        issues.append({
            'type': 'duplicate_slugs',
            'count': dup_slugs.count(),
            'model': 'Destination',
        })

    return issues


def check_inconsistent_data():
    """Check for inconsistent data.

    Returns:
        List of issues
    """
    issues = []

    # Reviews with invalid ratings
    invalid_ratings = Rating.objects.filter(
        Q(value__lt=1) | Q(value__gt=5)
    )
    if invalid_ratings.exists():
        issues.append({
            'type': 'invalid_ratings',
            'count': invalid_ratings.count(),
        })

    # Hotels with negative prices
    negative_prices = Hotel.objects.filter(price_per_night__lt=0)
    if negative_prices.exists():
        issues.append({
            'type': 'negative_prices',
            'count': negative_prices.count(),
        })

    return issues


def check_missing_images():
    """Check for destinations without images.

    Returns:
        List of issues
    """
    issues = []

    dests_without_images = Destination.publicly_visible().filter(
        gallery__isnull=True
    ).distinct()

    if dests_without_images.exists():
        issues.append({
            'type': 'missing_images',
            'count': dests_without_images.count(),
            'model': 'Destination',
        })

    return issues


def _generate_recommendations(checks):
    """Generate recommendations based on check results.

    Args:
        checks: Dict with check results

    Returns:
        List of recommendations
    """
    recommendations = []

    if checks.get('missing_fields'):
        recommendations.append({
            'priority': 'high',
            'action': 'Fill missing required fields',
            'details': 'Some records are missing required fields like name or coordinates',
        })

    if checks.get('invalid_coordinates'):
        recommendations.append({
            'priority': 'high',
            'action': 'Fix invalid coordinates',
            'details': 'Some destinations have coordinates outside Nepal or at null island',
        })

    if checks.get('orphaned_records'):
        recommendations.append({
            'priority': 'medium',
            'action': 'Clean up orphaned records',
            'details': 'Some images or hotels are not linked to any destination',
        })

    if checks.get('duplicate_entries'):
        recommendations.append({
            'priority': 'medium',
            'action': 'Merge duplicate entries',
            'details': 'Some destinations have duplicate names or slugs',
        })

    if checks.get('missing_images'):
        recommendations.append({
            'priority': 'low',
            'action': 'Add images to destinations',
            'details': 'Some destinations have no images in their gallery',
        })

    return recommendations
