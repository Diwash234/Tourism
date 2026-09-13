"""
Object-storage abstraction for generated images.

Saves images to ``MEDIA_ROOT/ai_generated/...`` by default (local disk,
works out of the box). The same interface is implemented for S3-compatible
storage (AWS S3 / Cloudflare R2 / MinIO) via django-storages -- set
``IMAGE_STORAGE_BACKEND=s3`` and the usual AWS_* / R2_* env vars to use it.

The local backend also generates a thumbnail with Pillow when available.
"""
from __future__ import annotations
import io
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@dataclass
class StoredImage:
    url: str
    path: str
    thumbnail_url: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    format: str = "webp"


class LocalStorage:
    folder = "ai_generated"

    def save(self, data: bytes, filename: str = None, ext: str = "webp") -> StoredImage:
        from django.core.files.storage import default_storage
        name = filename or f"{uuid.uuid4().hex}.{ext}"
        rel = os.path.join(self.folder, name)
        path = default_storage.save(rel, ContentFile(data))
        url = default_storage.url(path)

        thumb_url = ""
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data)).convert("RGB")
            img.thumbnail((480, 480))
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=82)
            tname = f"{os.path.splitext(name)[0]}_thumb.webp"
            tpath = default_storage.save(os.path.join(self.folder, "thumbs", tname), ContentFile(buf.getvalue()))
            thumb_url = default_storage.url(tpath)
        except Exception as exc:  # noqa: BLE001
            logger.debug("thumbnail generation skipped: %s", exc)

        return StoredImage(url=url, path=path, thumbnail_url=thumb_url, format=ext)


class S3Storage:
    """S3 / R2 / MinIO via django-storages. Configure AWS_* env vars."""
    def save(self, data: bytes, filename: str = None, ext: str = "webp") -> StoredImage:
        from storages.backends.s3boto3 import S3Boto3Storage  # type: ignore
        storage = S3Boto3Storage()
        name = filename or f"{uuid.uuid4().hex}.{ext}"
        path = storage.save(f"ai_generated/{name}", ContentFile(data))
        return StoredImage(url=storage.url(path), path=path, format=ext)


def get_storage():
    backend = getattr(settings, "IMAGE_STORAGE_BACKEND", "local").lower()
    if backend == "s3":
        return S3Storage()
    return LocalStorage()


def store_from_url(url: str) -> Optional[StoredImage]:
    """Download a remote generated image and persist it via the storage backend."""
    import requests
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not download generated image %s: %s", url[:80], exc)
        return None
    return get_storage().save(resp.content)
