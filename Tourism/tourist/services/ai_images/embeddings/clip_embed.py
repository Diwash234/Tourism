"""
Vision-language embeddings for semantic search and destination matching.

Uses ``sentence-transformers`` (CLIP / SigLIP / DINOv2) if installed.
Otherwise falls back to a deterministic TF-IDF over destination text so the
search API still returns useful results. The public functions return plain
Python lists so they can be JSON-serialised / stored in any backend.
"""
from __future__ import annotations
import logging
import math
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_NAME = "clip-ViT-B-32"


def _model():
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer(_MODEL_NAME)
        except Exception as exc:  # noqa: BLE001
            logger.warning("sentence-transformers unavailable, using TF-IDF fallback: %s", exc)
            _MODEL = False
    return _MODEL


def embed_text(text: str) -> List[float]:
    m = _model()
    if m:
        vec = m.encode(text or "", convert_to_numpy=True, normalize_embeddings=True)
        return [float(x) for x in vec]
    return _tfidf_embed(text or "")


def embed_image(image_bytes: bytes) -> Optional[List[float]]:
    m = _model()
    if not m:
        return None
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        vec = m.encode(img, convert_to_numpy=True, normalize_embeddings=True)
        return [float(x) for x in vec]
    except Exception as exc:  # noqa: BLE001
        logger.warning("image embedding failed: %s", exc)
        return None


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def clip_text_similarity(a: str, b: str) -> float:
    return cosine(embed_text(a), embed_text(b))


# ---- deterministic TF-IDF fallback (no external ML deps) -----------------
_VOCAB = None


def _tokens(text: str):
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2]


def _tfidf_embed(text: str, dim: int = 256) -> List[float]:
    global _VOCAB
    if _VOCAB is None:
        # Build a fixed tourism vocabulary so vectors are stable.
        words = ("nepal kathmandu pokhara everest annapurna himalaya temple stupa "
                 "monastery lake mountain himalayan trekking trail pagoda durbar "
                 "buddha hindu heritage monastery gompa lumbini chitwan rhino jungle "
                 "terai mustang manang rara gosaikunda sarangkot nagarkot bandipur "
                 "ilam khaptad bardiya koshi janakpur patan bhaktapur pashupatinath "
                 "boudhanath swayambhunath thamel prayer flags rhododendron glacier "
                 "village ridge valley river forest hill sunrise sunset snow monastery "
                 "newari sherpa gurung tharu mithila culture festival food market").split()
        _VOCAB = {w: i for i, w in enumerate(words)}
    vec = [0.0] * dim
    for tok in _tokens(text):
        if tok in _VOCAB:
            vec[_VOCAB[tok] % dim] += 1.0
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]
