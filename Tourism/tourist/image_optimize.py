"""Optional optimisation for admin image uploads.

Used by the Media Library upload when the operator ticks "Optimise" (the
API default is off, so existing clients keep storing the original bytes).

What it does:
- applies the EXIF orientation, then drops all metadata (camera data and any
  GPS location embedded in the photo);
- scales the longest side down to ``max_side`` (never up);
- re-encodes as WebP.

The original is kept whenever optimisation would not make the file smaller,
and GIFs are never touched (re-encoding would drop animation frames).
"""
from __future__ import annotations

import io
import os

from django.core.files.base import ContentFile

DEFAULT_MAX_SIDE = 2560
DEFAULT_QUALITY = 82


def wants_optimisation(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def optimise_image_upload(uploaded, *, max_side: int = DEFAULT_MAX_SIDE, quality: int = DEFAULT_QUALITY):
    """Return ``(file, report)``. ``file`` is either a new WebP ContentFile or
    the untouched upload; ``report`` says what happened, for the API reply."""
    from PIL import Image, ImageOps

    original_size = getattr(uploaded, "size", None)
    uploaded.seek(0)
    try:
        with Image.open(uploaded) as source:
            if source.format == "GIF":
                uploaded.seek(0)
                return uploaded, {"optimised": False, "reason": "GIF images are stored unchanged"}
            image = ImageOps.exif_transpose(source)
            width, height = image.size
            if max(width, height) > max_side:
                image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            has_alpha = image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info)
            image = image.convert("RGBA" if has_alpha else "RGB")
            buffer = io.BytesIO()
            # No exif/icc arguments: WebP output carries no metadata.
            image.save(buffer, format="WEBP", quality=quality, method=6)
    except Exception:  # noqa: BLE001 - never block an upload that already passed validation
        uploaded.seek(0)
        return uploaded, {"optimised": False, "reason": "Image could not be re-encoded; original stored"}

    data = buffer.getvalue()
    if original_size is not None and len(data) >= original_size:
        uploaded.seek(0)
        return uploaded, {"optimised": False, "reason": "Original is already smaller; stored unchanged",
                          "original_bytes": original_size}

    stem = os.path.splitext(os.path.basename(getattr(uploaded, "name", "") or "image"))[0] or "image"
    return ContentFile(data, name=f"{stem}.webp"), {
        "optimised": True,
        "original_bytes": original_size,
        "stored_bytes": len(data),
        "width": image.size[0],
        "height": image.size[1],
        "format": "WEBP",
    }
