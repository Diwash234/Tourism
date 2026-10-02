"""Data export pipeline.

Provides:
- Export data in multiple formats (JSON, CSV, XML)
- Support incremental exports
- Support scheduled exports
- Export statistics
"""
import csv
import json
import logging
from datetime import timedelta
from io import StringIO

from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache

from .models import Destination, Hotel, Booking, Review, User

logger = logging.getLogger(__name__)


def export_destinations(format='json', filters=None):
    """Export destinations.

    Args:
        format: Export format ('json', 'csv', 'xml')
        filters: Optional filters

    Returns:
        Exported data as string
    """
    try:
        queryset = Destination.publicly_visible()

        if filters:
            if filters.get('district'):
                queryset = queryset.filter(district=filters['district'])
            if filters.get('province'):
                queryset = queryset.filter(province=filters['province'])
            if filters.get('category'):
                queryset = queryset.filter(category_id=filters['category'])

        if format == 'json':
            return _export_json(queryset)
        elif format == 'csv':
            return _export_csv(queryset)
        elif format == 'xml':
            return _export_xml(queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")

    except Exception as exc:
        logger.error(f"Error exporting destinations: {exc}")
        return None


def export_hotels(format='json', filters=None):
    """Export hotels.

    Args:
        format: Export format
        filters: Optional filters

    Returns:
        Exported data as string
    """
    try:
        queryset = Hotel.objects.filter(is_active=True)

        if filters:
            if filters.get('destination'):
                queryset = queryset.filter(destination_id=filters['destination'])

        if format == 'json':
            return _export_json(queryset)
        elif format == 'csv':
            return _export_csv(queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")

    except Exception as exc:
        logger.error(f"Error exporting hotels: {exc}")
        return None


def export_bookings(format='json', filters=None):
    """Export bookings.

    Args:
        format: Export format
        filters: Optional filters

    Returns:
        Exported data as string
    """
    try:
        queryset = Booking.objects.all()

        if filters:
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('date_from'):
                queryset = queryset.filter(check_in__gte=filters['date_from'])
            if filters.get('date_to'):
                queryset = queryset.filter(check_out__lte=filters['date_to'])

        if format == 'json':
            return _export_json(queryset)
        elif format == 'csv':
            return _export_csv(queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")

    except Exception as exc:
        logger.error(f"Error exporting bookings: {exc}")
        return None


def export_reviews(format='json', filters=None):
    """Export reviews.

    Args:
        format: Export format
        filters: Optional filters

    Returns:
        Exported data as string
    """
    try:
        queryset = Review.objects.filter(moderation_status='approved')

        if filters:
            if filters.get('destination'):
                queryset = queryset.filter(destination_id=filters['destination'])
            if filters.get('rating'):
                queryset = queryset.filter(rating__gte=filters['rating'])

        if format == 'json':
            return _export_json(queryset)
        elif format == 'csv':
            return _export_csv(queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")

    except Exception as exc:
        logger.error(f"Error exporting reviews: {exc}")
        return None


def get_export_stats():
    """Get export statistics.

    Returns:
        Dict with export statistics
    """
    return {
        'destinations': Destination.objects.count(),
        'hotels': Hotel.objects.count(),
        'bookings': Booking.objects.count(),
        'reviews': Review.objects.count(),
        'users': User.objects.count(),
    }


def _export_json(queryset):
    """Export queryset as JSON.

    Args:
        queryset: Django QuerySet

    Returns:
        JSON string
    """
    data = []
    for obj in queryset:
        item = {}
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if value is not None:
                item[field.name] = str(value)
        data.append(item)
    return json.dumps(data, indent=2, default=str)


def _export_csv(queryset):
    """Export queryset as CSV.

    Args:
        queryset: Django QuerySet

    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    fields = [f.name for f in queryset.model._meta.fields]
    writer.writerow(fields)

    # Write data
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field)
            row.append(str(value) if value is not None else '')
        writer.writerow(row)

    return output.getvalue()


def _export_xml(queryset):
    """Export queryset as XML.

    Args:
        queryset: Django QuerySet

    Returns:
        XML string
    """
    from xml.etree.ElementTree import Element, SubElement, tostring

    root = Element('data')

    for obj in queryset:
        item = SubElement(root, 'item')
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if value is not None:
                field_elem = SubElement(item, field.name)
                field_elem.text = str(value)

    return tostring(root, encoding='unicode')
