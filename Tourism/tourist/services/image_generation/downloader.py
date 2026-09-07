"""
Downloads AI-generated images and stores them locally, trying multiple
providers until a valid image is returned.

This is what prevents the "colored box with text" placeholder: we
download the bytes, verify they're a real JPEG/PNG/WebP of sufficient size,
and only then save them as actual files referenced by DestinationImage.
If a provider returns an error/placeholder, we try the next model.
"""
from __future__ import annotations
import io
import logging
import os
import time
import uuid
from typing import List, Optional

import requests
from django.conf import settings
from django.core.files.base import ContentFile

from .providers import build_candidates

logger = logging.getLogger(__name__)

MIN_BYTES = 8_000           # below this it's almost certainly an error image
TIMEOUT = 45
VALID_MIME = {"image/jpeg", "image/png", "image/webp"}


def _looks_like_real_image(data: bytes) -> bool:
    """Reject tiny files / HTML error pages / SVG placeholders."""
    if len(data) < MIN_BYTES:
        return False
    if data[:1] == b"<" or b"<html" in data[:200].lower():
        return False
    # JPEG magic FF D8, PNG 89 50 4E 47, WebP RIFF....WEBP
    return (
        data[:2] == b"\xff\xd8"
        or data[:4] == b"\x89PNG"
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )


def _download(url: str) -> Optional[bytes]:
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (NepalTourismPlatform)",
            "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*",
        })
        if r.status_code == 200 and _looks_like_real_image(r.content):
            return r.content
        logger.info("reject %s: status=%s size=%s", url[:80], r.status_code, len(r.content))
    except Exception as exc:  # noqa: BLE001
        logger.info("download failed %s: %s", url[:80], exc)
    return None


def _save_to_media(data: bytes, dest_id, idx: int) -> str:
    """Persist bytes under MEDIA_ROOT/ai_generated/ and return the relative path."""
    ext = "webp" if data[:4] == b"RIFF" else "png" if data[:4] == b"\x89PNG" else "jpg"
    folder = os.path.join("ai_generated", str(dest_id))
    name = f"{uuid.uuid4().hex}_{idx}.{ext}"
    rel = os.path.join(folder, name)
    storage_path = os.path.join(settings.MEDIA_ROOT, rel)
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    with open(storage_path, "wb") as f:
        f.write(data)
    return rel


def fetch_image(destination, idx: int = 0) -> Optional[dict]:
    """
    Build candidate URLs for this destination across providers and try each
    until one downloads as a real image. Returns metadata dict or None.
    """
    candidates = build_candidates(destination, num=12)
    if idx >= len(candidates):
        idx = idx % len(candidates)
    # Rotate starting point by idx so each image tries a different provider first
    ordered = candidates[idx:] + candidates[:idx]
    for cand in ordered:
        data = _download(cand["url"])
        if data:
            path = _save_to_media(data, destination.id or "x", idx)
            return {**cand, "file_path": path, "bytes": len(data)}
        time.sleep(0.3)
    return None


def fetch_images(destination, num: int = 10) -> List[dict]:
    """Download up to num distinct valid images for a destination."""
    results = []
    for i in range(num):
        img = fetch_image(destination, idx=i)
        if img:
            results.append(img)
    return results
