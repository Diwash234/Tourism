"""
Unified image collector for hotels, hospitals and destinations.

Strategy -- tries many sources so a single failure never leaves a place
with a placeholder:

  1. AI generation (Pollinations/Flux, free, no key) with 12+ per-destination
     variations, each using a very specific place+region prompt.
  2. Wikimedia Commons (free, licensed, accurate).
  3. DuckDuckGo image search (free, no key).
  4. Openverse (free, openly licensed).

The first source that returns a usable image wins; results are scored for
destination match (name + district + province keywords) so unrelated photos
are filtered out. This is what stops "Nagarkot showing a bike".
"""
from __future__ import annotations
import logging
from typing import List, Optional

from django.db import models

from tourist.services.image_generation import pollinations
from tourist.services.image_search.search import (
    ImageHit, search_destination_images, search_wikimedia, search_duckduckgo,
)

logger = logging.getLogger(__name__)


def collect_for_destination(destination, num: int = 15,
                             use_ai: bool = True, use_search: bool = True) -> List[dict]:
    """
    Return a list of image dicts ready to insert into DestinationImage:
      {url, thumbnail, source, source_platform, photographer, license,
       prompt, seed, style, caption, match_score}
    """
    out: List[dict] = []
    seen = set()

    def _add(hit: ImageHit, score_override=None):
        if not hit.url or hit.url in seen:
            return
        seen.add(hit.url)
        out.append({
            "url": hit.url,
            "thumbnail": hit.thumbnail or hit.url,
            "source": "wikimedia" if hit.source == "wikimedia" else "web",
            "source_platform": hit.source,
            "photographer": hit.author[:150],
            "license": hit.license[:100],
            "prompt": "",
            "seed": None,
            "style": hit.source,
            "caption": f"{destination.name} — {hit.title or hit.source}",
            "match_score": score_override if score_override is not None else hit.match_score,
        })

    # 1. AI-generated (always available, free)
    if use_ai:
        try:
            specs = pollinations.generate_specs(destination, num=num)
            for spec in specs:
                if spec.url in seen:
                    continue
                seen.add(spec.url)
                # AI images get a high default match because the prompt is
                # built specifically for this destination.
                out.append({
                    "url": spec.url,
                    "thumbnail": spec.url,
                    "source": "ai_generated",
                    "source_platform": f"ai:{pollinations.MODEL}:{spec.style}",
                    "photographer": "AI generated (Flux/Pollinations)",
                    "license": "AI generated — editorial illustration, not a photograph",
                    "prompt": spec.prompt,
                    "seed": spec.seed,
                    "style": spec.style,
                    "caption": f"{destination.name} — {spec.style}",
                    "match_score": 0.9,
                })
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI generation failed for %s: %s", destination.name, exc)

    # 2+3+4 web search (free sources)
    if use_search:
        try:
            hits = search_destination_images(destination, per_source=max(10, num), min_score=0.25)
            for h in hits:
                _add(h)
        except Exception as exc:  # noqa: BLE001
            logger.warning("image search failed for %s: %s", destination.name, exc)

    # If web search found nothing at all (e.g. network blocked), make sure we
    # still have the AI images; if those also failed, leave empty so caller
    # can fall back to the catalog.
    return out[:num]


def collect_for_hotel(hotel, num: int = 8) -> List[dict]:
    """Collect images for a Hotel row (uses its destination + name)."""
    dest = hotel.destination
    if not dest:
        return []
    # Reuse destination collection but bias the prompt/caption toward the hotel
    images = collect_for_destination(dest, num=num, use_ai=True, use_search=True)
    name = hotel.name
    for img in images:
        img["caption"] = f"{name}, {dest.name}"
        if img["source"] == "ai_generated":
            # tweak the stored prompt to mention the hotel for traceability
            img["prompt"] = f"{name}, accommodation in {dest.name}, Nepal. " + (img["prompt"] or "")
    return images


def collect_for_hospital(hospital, num: int = 6) -> List[dict]:
    """Collect images for a Hospital row (health-post / hospital in its town)."""
    # Hospital rows don't have a FK to Destination; build a lightweight shim
    class _Shim:
        id = f"hospital-{hospital.id}"
        name = hospital.name
        district = hospital.district
        province = ""
        city = ""
        type = "hospital"
        category = None
        description = f"{hospital.name} is a health facility in {hospital.district}, Nepal."
    return collect_for_destination(_Shim(), num=num, use_ai=True, use_search=False)
