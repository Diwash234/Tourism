"""
API versioning support for the Tourism platform.
"""
import logging

from rest_framework.versioning import URLPathVersioning

logger = logging.getLogger(__name__)


class APIVersioning(URLPathVersioning):
    """
    API versioning via URL path: /api/v1/, /api/v2/, etc.
    """
    default_version = "v1"
    allowed_versions = ["v1", "v2"]
    version_param = "version"


def get_api_version(request):
    """Get the current API version from the request."""
    return getattr(request, "version", "v1")


def version_features(version):
    """Get feature flags for a specific API version."""
    features = {
        "v1": {
            "basic_search": True,
            "advanced_search": False,
            "recommendations": True,
            "real_time_notifications": False,
            "analytics": False,
        },
        "v2": {
            "basic_search": True,
            "advanced_search": True,
            "recommendations": True,
            "real_time_notifications": True,
            "analytics": True,
        },
    }
    return features.get(version, features["v1"])
