"""
Custom validators for the Tourism API.
"""
import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class PhoneNumberValidator:
    """Validates phone numbers in international format."""

    message = "Enter a valid phone number in international format (e.g., +97798XXXXXXXX)."
    code = "invalid_phone"

    def __call__(self, value):
        if not value:
            return
        # Allow +97798XXXXXXXX or +1XXXXXXXXXX
        pattern = r"^\+\d{10,15}$"
        if not re.match(pattern, str(value)):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


@deconstructible
class CoordinateValidator:
    """Validates latitude and longitude values."""

    message = "Invalid coordinate value."
    code = "invalid_coordinate"

    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, value):
        if value is None:
            return
        try:
            val = float(value)
            if not (self.min_value <= val <= self.max_value):
                raise ValidationError(self.message, code=self.code)
        except (TypeError, ValueError):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.min_value == other.min_value
            and self.max_value == other.max_value
        )


class PasswordStrengthValidator:
    """Validates password strength beyond Django's defaults."""

    message = "Password is too weak. It must contain uppercase, lowercase, digit, and special character."
    code = "weak_password"

    def __call__(self, value):
        if not value:
            return
        errors = []
        if not re.search(r"[A-Z]", value):
            errors.append("uppercase letter")
        if not re.search(r"[a-z]", value):
            errors.append("lowercase letter")
        if not re.search(r"\d", value):
            errors.append("digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            errors.append("special character")
        if errors:
            raise ValidationError(
                f"Password must contain at least one: {', '.join(errors)}.",
                code=self.code,
            )

    def __eq__(self, other):
        return isinstance(other, self.__class__)


def validate_image_extension(value):
    """Validate that an uploaded file has an allowed image extension."""
    import os
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
    if ext not in valid_extensions:
        raise ValidationError(
            f"Unsupported file extension '{ext}'. Allowed: {', '.join(valid_extensions)}"
        )


def validate_file_size(value, max_size_mb=50):
    """Validate that an uploaded file does not exceed the size limit."""
    max_size = max_size_mb * 1024 * 1024
    if value.size > max_size:
        raise ValidationError(f"File size exceeds {max_size_mb} MB limit.")
