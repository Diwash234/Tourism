"""
Template context processors for the Tourism platform.
"""
from django.conf import settings


def site_settings(request):
    """Add site settings to template context."""
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Nepal Tourism Platform"),
        "SITE_URL": getattr(settings, "PUBLIC_SITE_URL", ""),
        "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
    }


def api_info(request):
    """Add API information to template context."""
    return {
        "API_VERSION": "v1",
        "API_BASE_URL": getattr(settings, "BACKEND_URL", "") + "/api/v1/",
    }


def feature_flags(request):
    """Add feature flags to template context."""
    from .config import FeatureFlags
    return {
        "FEATURE_FLAGS": FeatureFlags.get_all(),
    }
