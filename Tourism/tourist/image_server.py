"""
Tourism/tourist/image_server.py

Helpers for the standalone image server.

Django stores only *paths* in the database (``DestinationImage.image_path``,
e.g. ``nepal/kathmandu/001.webp``). The binary lives on the image server
(dev: ``python -m http.server`` in ``image-server/``, prod: Nginx). This module
builds the public URL from the configurable ``IMAGE_BASE_URL`` and knows how to
normalize a path for storage.
"""
import posixpath
import re
from urllib.parse import urljoin

from django.conf import settings

# Supported image extensions (lowercase, with dot) used by the import command.
SUPPORTED_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png", ".gif", ".avif"}


def normalize_image_path(path: str) -> str:
    """Normalize a relative image path for storage.

    - strips any leading slashes / ``images/`` prefix / URL junk;
    - converts OS separators to forward slashes;
    - lowercases nothing (filenames on the image server may be case-sensitive).
    """
    if not path:
        return ""
    p = path.replace("\\", "/").strip()
    # strip scheme/host if someone pasted a full URL
    if "://" in p:
        p = p.split("://", 1)[1]
        p = p.split("/", 1)[1] if "/" in p else ""
    # strip a leading images/ prefix (it is implied by the URL builder)
    p = re.sub(r"^/+", "", p)
    if p.startswith("images/"):
        p = p[len("images/"):]
    p = re.sub(r"^/+", "", p)
    return posixpath.normpath(p)


def image_server_url(path: str) -> str:
    """Return the public URL for a stored image path.

    >>> image_server_url("nepal/kathmandu/001.webp")
    'http://localhost:8000/images/nepal/kathmandu/001.webp'
    """
    if not path:
        return ""
    base = (settings.IMAGE_BASE_URL or "http://localhost:8000").rstrip("/")
    return f"{base}/images/{posixpath.normpath(path.lstrip('/'))}"


def is_supported_image(filename: str) -> bool:
    """True when the file has a supported image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS
    }


def guess_alt_text(path: str, fallback: str = "") -> str:
    """Build a readable alt text from a path (e.g. nepal/kathmandu/001.webp)."""
    stem = posixpath.splitext(posixpath.basename(path.replace("\\", "/")))[0]
    stem = re.sub(r"[_-]+", " ", stem).strip()
    if stem:
        return stem[:255]
    return (fallback or "")[:255]
