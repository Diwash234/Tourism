"""
Perceptual hashing and near-duplicate detection.

Uses pHash (DCT-based) when Pillow is available; falls back to a simple
aHash so the system still works without optional dependencies.
"""
from __future__ import annotations
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def phash_distance(a: str, b: str) -> int:
    if not a or not b or len(a) != len(b):
        return 64
    return _hamming(a, b)


def compute_phash(image_bytes: bytes) -> Optional[str]:
    """Return a 16-char hex pHash, or None if image can't be decoded."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return _ahash_fallback(image_bytes)

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((32, 32), Image.LANCZOS)
        arr = np.asarray(img, dtype=float)
        dct = _dct2(arr)
        low = dct[:8, :8]
        med = (low.sum() - low[0, 0]) / 63.0
        bits = (low > med).flatten()
        return "".join("1" if b else "0" for b in bits).zfill(64)
    except Exception as exc:  # noqa: BLE001
        logger.warning("pHash failed: %s", exc)
        return _ahash_fallback(image_bytes)


def _dct2(a):
    try:
        from scipy.fftpack import dct
        return dct(dct(a, axis=0, norm="ortho"), axis=1, norm="ortho")
    except ImportError:
        # Very small 32x32 plain-numpy DCT fallback.
        import numpy as np
        N = a.shape[0]
        n = np.arange(N)
        k = n.reshape((N, 1))
        c = np.cos(np.pi * (2 * n + 1) * k / (2 * N))
        c[0] *= 1 / np.sqrt(2)
        c *= np.sqrt(2 / N)
        return c @ a @ c.T


def _ahash_fallback(image_bytes: bytes) -> Optional[str]:
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((8, 8))
        arr = np.asarray(img, dtype=float)
        bits = (arr > arr.mean()).flatten()
        v = 0
        for b in bits:
            v = (v << 1) | int(b)
        return f"{v:016x}"
    except Exception:
        return None


def is_near_duplicate(phash: str, existing_hashes, threshold: int = 8) -> bool:
    """True if phash is within `threshold` bits of any existing hash."""
    if not phash:
        return False
    return any(phash_distance(phash, h) <= threshold for h in existing_hashes if h)
