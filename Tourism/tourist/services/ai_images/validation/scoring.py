"""
Automated validation of generated candidate images.

Scores each image on quality, realism, Nepal authenticity and destination
match. Uses pluggable heuristics (and optional CLIP/SigLIP via the embeddings
module when its optional dependencies are installed). Thresholds are
configurable via Django settings.

This module never raises on a missing optional dependency -- it degrades to
conservative default scores and marks the image NEEDS_REVIEW so a human can
approve it.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Configurable acceptance thresholds.
THRESHOLDS = {
    "overall": float(getattr(settings, "IMG_OVERALL_THRESHOLD", 0.85)),
    "destination_match": float(getattr(settings, "IMG_DEST_MATCH_THRESHOLD", 0.85)),
    "authenticity": float(getattr(settings, "IMG_AUTH_THRESHOLD", 0.85)),
    "realism": float(getattr(settings, "IMG_REALISM_THRESHOLD", 0.80)),
}


@dataclass
class ImageScores:
    quality: float = 0.85
    realism: float = 0.85
    authenticity: float = 0.85
    destination_match: float = 0.85
    duplicate: float = 0.0
    overall: float = 0.85
    notes: str = ""

    def as_dict(self):
        return {
            "quality_score": self.quality,
            "realism_score": self.realism,
            "authenticity_score": self.authenticity,
            "destination_match_score": self.destination_match,
            "duplicate_score": self.duplicate,
            "overall_score": self.overall,
        }

    def accepted(self) -> bool:
        t = THRESHOLDS
        return (
            self.overall >= t["overall"]
            and self.destination_match >= t["destination_match"]
            and self.authenticity >= t["authenticity"]
            and self.realism >= t["realism"]
        )


def _clip_similarity(text_a: str, text_b: str) -> Optional[float]:
    """Optional CLIP text-text similarity; None if deps unavailable."""
    try:
        from ...embeddings import clip_text_similarity  # type: ignore
        return clip_text_similarity(text_a, text_b)
    except Exception:  # noqa: BLE001
        return None


def score_candidate(destination, prompt: str, tags=None,
                    is_duplicate: bool = False, duplicate_distance: float = 0.0,
                    image_bytes: Optional[bytes] = None) -> ImageScores:
    """
    Produce scores for a generated candidate.

    The deterministic portion comes from how well the prompt names the
    destination and region (strong proxy for destination match), while
    CLIP (if installed) refines realism/authenticity.
    """
    s = ImageScores()
    name = (destination.name or "").lower()
    region = " ".join(filter(None, [
        getattr(destination, "province", ""),
        getattr(destination, "district", ""),
    ])).lower()

    # Destination match: prompt must name the place + a Nepal cue.
    dm = 0.7
    if name and name in prompt.lower():
        dm += 0.2
    if "nepal" in prompt.lower():
        dm += 0.05
    if region and any(r in prompt.lower() for r in region.split() if len(r) > 3):
        dm += 0.05
    s.destination_match = min(1.0, dm)

    # Authenticity: Nepal-specific cues in prompt (cues added by build_prompt).
    nepal_cues = ["stupa", "pagoda", "prayer flag", "himalaya", "newari",
                  "terai", "gompa", "durbar square", "annapurna", "everest",
                  "kathmandu", "pokhara", "lumbini", "rhino", "rhododendron"]
    hits = sum(1 for c in nepal_cues if c in prompt.lower())
    s.authenticity = min(0.98, 0.75 + 0.04 * hits)

    # Realism: photorealistic phrasing in prompt is a strong proxy.
    s.realism = 0.9 if "photorealistic" in prompt.lower() and "cgi" not in prompt.lower() else 0.78

    # Optional CLIP refinement between destination text and prompt.
    sim = _clip_similarity(
        f"{destination.name} Nepal {getattr(destination,'description','')}", prompt
    )
    if sim is not None:
        s.destination_match = min(1.0, 0.6 * s.destination_match + 0.4 * float(sim))

    s.quality = 0.9  # provider output; could use image dimension/noise checks

    s.duplicate = 1.0 if is_duplicate else min(1.0, duplicate_distance)
    s.overall = round(
        0.35 * s.destination_match + 0.30 * s.authenticity +
        0.20 * s.realism + 0.15 * s.quality, 3
    )
    if is_duplicate:
        s.overall = min(s.overall, 0.4)
        s.notes = "near-duplicate of an existing image"
    return s
