"""
API Versioning Middleware.

Adds deprecation warning headers to v1 API responses and supports
version negotiation via headers.

Headers added to v1 responses:
- Deprecation: true
- Sunset: <date>
- Link: <v2_url>; rel="successor-version"

Version negotiation:
- Clients can request a specific version via the X-API-Version header
- Default version is v1 (for backward compatibility)
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class APIVersioningMiddleware:
    """
    Middleware that adds API versioning headers and handles deprecation warnings.

    Add to MIDDLEWARE in settings.py:
        'tourist.api_versioning.APIVersioningMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only process API requests
        if not request.path.startswith("/api/"):
            return response

        # Determine the requested version from path
        version = self._get_version_from_path(request.path)

        if version and version in settings.API_VERSION_DEPRECATION_HEADERS:
            version_info = settings.API_VERSION_DEPRECATION_HEADERS[version]

            if version_info.get("deprecated"):
                response["Deprecation"] = "true"

                if version_info.get("sunset_date"):
                    response["Sunset"] = version_info["sunset_date"]

                if version_info.get("successor_version"):
                    successor = version_info["successor_version"]
                    # Build the successor URL
                    successor_url = request.path.replace(f"/api/{version}/", f"/api/{successor}/")
                    response["Link'] = f'<{successor_url}>; rel="successor-version"'

                # Log deprecated API usage
                logger.info(
                    f"Deprecated API version {version} accessed: {request.path} "
                    f"by {request.META.get('REMOTE_ADDR', 'unknown')}"
                )

        # Add current API version header
        response["X-API-Version"] = version or "v1"

        return response

    def _get_version_from_path(self, path):
        """Extract API version from the request path."""
        parts = path.split("/")
        for part in parts:
            if part.startswith("v") and part[1:].isdigit():
                return part
        return None


def get_api_version(request):
    """
    Get the API version for a request.

    Priority:
    1. X-API-Version header
    2. URL path version
    3. Default (v1)

    Returns:
        String version (e.g. "v1", "v2")
    """
    # Check header first
    header_version = request.META.get("HTTP_X_API_VERSION", "")
    if header_version:
        return header_version

    # Check path
    parts = request.path.split("/")
    for part in parts:
        if part.startswith("v") and part[1:].isdigit():
            return part

    # Default
    return "v1"


def is_version_deprecated(version):
    """Check if an API version is deprecated."""
    version_info = settings.API_VERSION_DEPRECATION_HEADERS.get(version, {})
    return version_info.get("deprecated", False)


def get_version_info(version):
    """Get deprecation info for an API version."""
    return settings.API_VERSION_DEPRECATION_HEADERS.get(version, {})
