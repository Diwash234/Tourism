"""
Free, no-billing image search across multiple public sources.

Searches (in priority order):
  1. Wikimedia Commons  - free, licensed (CC BY-SA / public domain), accurate
  2. DuckDuckGo Images  - broad web image search, no API key required
  3. Openverse          - openly-licensed images (optional API key)

Results are filtered so only images that mention the destination / district /
region keywords are kept -- this is what prevents "Janakpur photo showing up
under Mustang". Each result carries its source URL, author and license so the
admin can verify and attribute it.

Nothing here requires a paid/billed API. All providers are free.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "NepalTourismPlatform/1.0 (https://github.com/Diwash234/Tourism; image-search)"
TIMEOUT = 20


@dataclass
class ImageHit:
    url: str
    thumbnail: str = ""
    source: str = "wikimedia"          # wikimedia | duckduckgo | openverse
    source_page: str = ""
    author: str = ""
    license: str = ""
    title: str = ""
    width: int = 0
    height: int = 0
    match_score: float = 0.0
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Source 1: Wikimedia Commons
# ---------------------------------------------------------------------------
def search_wikimedia(query: str, limit: int = 15) -> List[ImageHit]:
    """Search Wikimedia Commons. Returns ImageHit list with attribution."""
    hits: List[ImageHit] = []
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search", "gsrsearch": f"{query} Nepal",
                "gsrlimit": min(limit, 40), "gsrnamespace": 6,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size|mime",
                "iiurlwidth": 1280,
            },
            headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT,
        )
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
        for page in pages.values():
            ii = (page.get("imageinfo") or [{}])[0]
            mime = ii.get("mime", "")
            if not mime.startswith("image/") or mime == "image/gif":
                continue
            if ii.get("mime") == "image/svg+xml":
                continue
            meta = ii.get("extmetadata") or {}
            hits.append(ImageHit(
                url=ii.get("thumburl") or ii.get("url", ""),
                thumbnail=ii.get("thumburl") or ii.get("url", ""),
                source="wikimedia",
                source_page=page.get("fullurl", ""),
                author=_strip_html(meta.get("Artist", {}).get("value", "")),
                license=meta.get("LicenseShortName", {}).get("value", "CC BY-SA"),
                title=page.get("title", ""),
                width=ii.get("thumbwidth") or ii.get("width") or 0,
                height=ii.get("thumbheight") or ii.get("height") or 0,
                source_page_url=ii.get("descriptionurl", ""),
            ))
    except Exception as exc:  # noqa: BLE001
        logger.info("wikimedia search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 2: DuckDuckGo image search (no key)
# ---------------------------------------------------------------------------
def search_duckduckgo(query: str, limit: int = 20) -> List[ImageHit]:
    """Use DuckDuckGo's instant-image endpoint (vqd token). No API key."""
    hits: List[ImageHit] = []
    try:
        sess = requests.Session()
        sess.headers.update({"User-Agent": USER_AGENT, "Referer": "https://duckduckgo.com/"})
        # 1. obtain a vqd token
        tok = sess.get("https://duckduckgo.com/", params={"q": query}, timeout=TIMEOUT)
        m = re.search(r'vqd=["\']?(\d+)', tok.text)
        vqd = m.group(1) if m else ""
        if not vqd:
            m2 = re.search(r'vqd=([\d-]+)&', tok.text)
            vqd = m2.group(1) if m2 else ""
        if not vqd:
            return hits
        # 2. call the image endpoint
        r = sess.get(
            "https://duckduckgo.com/i.js",
            params={"l": "wt-wt", "o": "json", "q": f"{query} Nepal",
                    "vqd": vqd, "f": ",,,", "p": "1"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        for item in (r.json().get("results") or [])[:limit]:
            if not item.get("image"):
                continue
            hits.append(ImageHit(
                url=item["image"],
                thumbnail=item.get("thumbnail", item["image"]),
                source="duckduckgo",
                source_page=item.get("url", ""),
                title=item.get("title", ""),
                width=item.get("width", 0),
                height=item.get("height", 0),
                author=item.get("source", ""),
                license="web image - verify license",
            ))
    except Exception as exc:  # noqa: BLE001
        logger.info("duckduckgo search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 3: Openverse (optional key, free)
# ---------------------------------------------------------------------------
def search_openverse(query: str, limit: int = 20, api_key: str = "") -> List[ImageHit]:
    hits: List[ImageHit] = []
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": f"{query} Nepal", "page_size": limit, "license_type": "all"},
            headers=headers, timeout=TIMEOUT,
        )
        r.raise_for_status()
        for item in (r.json().get("results") or []):
            hits.append(ImageHit(
                url=item.get("url", ""),
                thumbnail=item.get("thumbnail", item.get("url", "")),
                source="openverse",
                source_page=item.get("foreign_landing_url", ""),
                author=item.get("creator", ""),
                license=f"{item.get('license','')} {item.get('license_version','')}".strip(),
                title=item.get("title", ""),
                width=item.get("width", 0),
                height=item.get("height", 0),
            ))
    except Exception as exc:  # noqa: BLE001
        logger.info("openverse search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Matching / scoring
# ---------------------------------------------------------------------------
def _build_keywords(destination) -> List[str]:
    parts = [destination.name, getattr(destination, "district", ""),
             getattr(destination, "province", ""), getattr(destination, "city", ""),
             getattr(destination, "municipality", "")]
    cat = destination.category.name if getattr(destination, "category_id", None) else ""
    if cat:
        parts.append(cat)
    return [p.lower().strip() for p in parts if p and len(p.strip()) > 2]


def score_hit(hit: ImageHit, destination) -> float:
    """How likely is this image actually of this destination (0..1)."""
    kws = _build_keywords(destination)
    hay = " ".join([hit.title or "", hit.author or "", hit.source_page or "",
                    hit.license or ""]).lower()
    if not kws:
        return 0.4
    name = kws[0]
    score = 0.0
    # exact destination name in title/url is the strongest signal
    if name in hay:
        score += 0.55
    # any other keyword (district / province) adds confidence
    hits_kw = sum(1 for k in kws[1:] if k and k in hay)
    score += min(0.35, 0.12 * hits_kw)
    # source reliability bonus
    if hit.source == "wikimedia":
        score += 0.15
    elif hit.source == "openverse":
        score += 0.08
    # width sanity (avoid tiny icons)
    if hit.width and hit.width >= 600:
        score += 0.05
    return min(1.0, score)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def search_destination_images(destination, per_source: int = 12,
                               min_score: float = 0.35,
                               sources=("wikimedia", "duckduckgo", "openverse"),
                               openverse_key: str = "") -> List[ImageHit]:
    """
    Search every source, deduplicate, score against the destination, and
    return only images that pass the match threshold. This guarantees an
    image for Mustang is actually about Mustang, not Janakpur.
    """
    name = destination.name
    # Use a more specific query than just the name when we have region info.
    region_bits = [b for b in (getattr(destination, "district", ""),
                               getattr(destination, "province", "")) if b]
    query = name + (f", {region_bits[0]}" if region_bits else "")

    all_hits: List[ImageHit] = []
    if "wikimedia" in sources:
        all_hits += search_wikimedia(query, per_source)
    if "duckduckgo" in sources:
        all_hits += search_duckduckgo(query, per_source)
    if "openverse" in sources:
        all_hits += search_openverse(query, per_source, openverse_key)

    # dedupe by url
    seen = set()
    unique = []
    for h in all_hits:
        if not h.url or h.url in seen:
            continue
        seen.add(h.url)
        unique.append(h)

    # score and filter
    scored = []
    for h in unique:
        h.match_score = score_hit(h, destination)
        if h.match_score >= min_score:
            scored.append(h)

    scored.sort(key=lambda h: h.match_score, reverse=True)
    return scored


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()
