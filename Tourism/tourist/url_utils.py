"""
URL utilities for the Tourism API.
"""
from urllib.parse import urlencode, urljoin

from django.conf import settings


def build_absolute_url(path: str) -> str:
    """Build an absolute URL from a relative path."""
    base = getattr(settings, "PUBLIC_SITE_URL", "") or getattr(settings, "BACKEND_URL", "")
    return urljoin(base, path)


def build_image_url(image_path: str) -> str:
    """Build a full image URL from a relative path."""
    if not image_path:
        return ""
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path
    base = getattr(settings, "IMAGE_BASE_URL", "")
    return urljoin(base + "/", image_path)


def build_api_url(path: str, params: dict = None) -> str:
    """Build an API URL with optional query parameters."""
    url = build_absolute_url(f"/api/v1/{path}")
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def get_frontend_url(path: str = "") -> str:
    """Get the frontend URL for a given path."""
    base = getattr(settings, "FRONTEND_URL", "") or getattr(settings, "PUBLIC_SITE_URL", "")
    return urljoin(base + "/", path)
