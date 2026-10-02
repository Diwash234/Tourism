"""
Custom template tags for the Tourism platform.
"""
import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary in templates."""
    if hasattr(dictionary, "get"):
        return dictionary.get(key)
    return None


@register.filter
def multiply(value, arg):
    """Multiply two numbers in templates."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide two numbers in templates."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage in templates."""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def json_script(value):
    """Output a JSON script tag."""
    return mark_safe(json.dumps(value))


@register.simple_tag
def get_settings_value(name):
    """Get a Django setting value in templates."""
    from django.conf import settings
    return getattr(settings, name, "")


@register.filter
def truncate_chars(value, max_length):
    """Truncate a string to a specific length."""
    if len(value) > max_length:
        return value[:max_length] + "..."
    return value
