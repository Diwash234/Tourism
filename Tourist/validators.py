"""Custom validators for the tourism platform.

Provides:
- Coordinate validation
- Phone number validation
- URL validation
- File size validation
- Content type validation
"""
import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.conf import settings


def validate_nepal_coordinates(latitude, longitude):
    """Validate that coordinates are within Nepal's bounding box.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Raises:
        ValidationError: If coordinates are invalid
    """
    if latitude is None or longitude is None:
        return  # Allow null values

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        raise ValidationError("Coordinates must be numeric values")

    # Nepal bounding box
    NEPAL_LAT_MIN, NEPAL_LAT_MAX = 26.0, 31.0
    NEPAL_LON_MIN, NEPAL_LON_MAX = 80.0, 89.0

    if not (NEPAL_LAT_MIN <= lat <= NEPAL_LAT_MAX):
        raise ValidationError(
            f"Latitude {lat} is outside Nepal's range ({NEPAL_LAT_MIN}-{NEPAL_LAT_MAX})"
        )

    if not (NEPAL_LON_MIN <= lon <= NEPAL_LON_MAX):
        raise ValidationError(
            f"Longitude {lon} is outside Nepal's range ({NEPAL_LON_MIN}-{NEPAL_LON_MAX})"
        )

    # Check for null island
    if lat == 0 and lon == 0:
        raise ValidationError("Coordinates (0, 0) are not valid")


def validate_phone_number(phone):
    """Validate a phone number.

    Args:
        phone: Phone number string

    Raises:
        ValidationError: If phone number is invalid
    """
    if not phone:
        return  # Allow empty values

    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

    # Check for valid phone number pattern
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        raise ValidationError(f"Invalid phone number: {phone}")


def validate_image_url(url):
    """Validate an image URL.

    Args:
        url: URL string

    Raises:
        ValidationError: If URL is not a valid image URL
    """
    if not url:
        return  # Allow empty values

    # Check URL format
    URLValidator()(url)

    # Check for valid image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
    if not any(url.lower().endswith(ext) for ext in valid_extensions):
        # Allow URLs without extensions (e.g., CDN URLs)
        pass


def validate_file_size(file, max_size_mb=10):
    """Validate file size.

    Args:
        file: File object
        max_size_mb: Maximum file size in MB

    Raises:
        ValidationError: If file is too large
    """
    if not file:
        return

    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(
            f"File size {file.size / (1024*1024):.1f}MB exceeds maximum {max_size_mb}MB"
        )


def validate_latitude(latitude):
    """Validate a latitude value.

    Args:
        latitude: Latitude value

    Raises:
        ValidationError: If latitude is invalid
    """
    if latitude is None:
        return

    try:
        lat = float(latitude)
    except (TypeError, ValueError):
        raise ValidationError("Latitude must be a numeric value")

    if not (-90 <= lat <= 90):
        raise ValidationError(f"Latitude {lat} is out of range (-90 to 90)")


def validate_longitude(longitude):
    """Validate a longitude value.

    Args:
        longitude: Longitude value

    Raises:
        ValidationError: If longitude is invalid
    """
    if longitude is None:
        return

    try:
        lon = float(longitude)
    except (TypeError, ValueError):
        raise ValidationError("Longitude must be a numeric value")

    if not (-180 <= lon <= 180):
        raise ValidationError(f"Longitude {lon} is out of range (-180 to 180)")


def validate_rating(value):
    """Validate a rating value.

    Args:
        value: Rating value

    Raises:
        ValidationError: If rating is invalid
    """
    if value is None:
        return

    try:
        rating = float(value)
    except (TypeError, ValueError):
        raise ValidationError("Rating must be a numeric value")

    if not (1 <= rating <= 5):
        raise ValidationError(f"Rating {rating} is out of range (1 to 5)")


def validate_price(value):
    """Validate a price value.

    Args:
        value: Price value

    Raises:
        ValidationError: If price is invalid
    """
    if value is None:
        return

    try:
        price = float(value)
    except (TypeError, ValueError):
        raise ValidationError("Price must be a numeric value")

    if price < 0:
        raise ValidationError("Price cannot be negative")


def validate_positive_integer(value, field_name="Value"):
    """Validate that a value is a positive integer.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is not a positive integer
    """
    if value is None:
        return

    try:
        num = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be an integer")

    if num < 0:
        raise ValidationError(f"{field_name} must be non-negative")


def validate_json_field(value):
    """Validate that a value is valid JSON-serializable data.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If value is not JSON-serializable
    """
    if value is None:
        return

    import json
    try:
        json.dumps(value)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid JSON data: {e}")


def validate_slug(value):
    """Validate a slug value.

    Args:
        value: Slug string

    Raises:
        ValidationError: If slug is invalid
    """
    if not value:
        return

    if not re.match(r'^[a-z0-9-]+$', value):
        raise ValidationError(
            "Slug can only contain lowercase letters, numbers, and hyphens"
        )

    if value.startswith('-') or value.endswith('-'):
        raise ValidationError("Slug cannot start or end with a hyphen")

    if '--' in value:
        raise ValidationError("Slug cannot contain consecutive hyphens")
