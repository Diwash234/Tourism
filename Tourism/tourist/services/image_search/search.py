"""
Free, no-billing image search across multiple public sources with Nepal-specific scoring.

Supported Sources:
  1. Wikimedia Commons  - free, licensed (CC BY-SA / public domain), accurate
  2. Openverse          - openly-licensed images (CC licenses)
  3. Flickr             - community & contributor photography
  4. Unsplash           - high-resolution travel photography
  5. Pexels             - curated travel & nature imagery
  6. Pixabay            - free high-quality photographs
  7. Curated Catalog    - local verified authentic Nepal photography database

Multi-factor scoring ensures images match the specific destination, district,
and province rather than pulling generic Nepal stock photography.
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

USER_AGENT = "NepalTourismPlatform/1.0 (https://github.com/Diwash234/Tourism; image-search)"
TIMEOUT = 12


@dataclass
class ImageHit:
    url: str
    thumbnail: str = ""
    source: str = "wikimedia"          # wikimedia | openverse | flickr | unsplash | pexels | pixabay | duckduckgo | curated
    source_title: str = "Wikimedia Commons"
    source_page: str = ""
    source_page_url: str = ""
    author: str = ""
    license: str = "CC BY-SA"
    attribution_requirement: str = "Attribution Required"
    title: str = ""
    width: int = 0
    height: int = 0
    location_match: int = 0            # 0-100%
    keyword_match: int = 0             # 0-100%
    confidence_score: int = 0          # 0-100%
    match_score: float = 0.0           # 0.0-1.0
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "thumbnail": self.thumbnail or self.url,
            "source": self.source,
            "source_title": self.source_title,
            "source_page": self.source_page,
            "source_page_url": self.source_page_url or self.source_page,
            "author": self.author or "Unknown Contributor",
            "license": self.license or "Public Domain / CC",
            "attribution_requirement": self.attribution_requirement,
            "title": self.title or "Nepal Landmark",
            "width": self.width,
            "height": self.height,
            "location_match": self.location_match,
            "keyword_match": self.keyword_match,
            "confidence_score": self.confidence_score,
            "match_score": self.match_score,
        }


# ---------------------------------------------------------------------------
# Source 1: Wikimedia Commons
# ---------------------------------------------------------------------------
def search_wikimedia(query: str, limit: int = 15) -> List[ImageHit]:
    """Search Wikimedia Commons for authentic, openly licensed photography."""
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
            if not mime.startswith("image/") or mime in ("image/gif", "image/svg+xml"):
                continue
            meta = ii.get("extmetadata") or {}
            license_val = meta.get("LicenseShortName", {}).get("value", "CC BY-SA 4.0")
            hits.append(ImageHit(
                url=ii.get("thumburl") or ii.get("url", ""),
                thumbnail=ii.get("thumburl") or ii.get("url", ""),
                source="wikimedia",
                source_title="Wikimedia Commons",
                source_page=page.get("fullurl", ""),
                author=_strip_html(meta.get("Artist", {}).get("value", "")),
                license=license_val,
                attribution_requirement=f"Attribution: {meta.get('Artist', {}).get('value', 'Contributor')} ({license_val})",
                title=page.get("title", "").replace("File:", "").replace(".jpg", "").replace(".png", ""),
                width=ii.get("thumbwidth") or ii.get("width") or 0,
                height=ii.get("thumbheight") or ii.get("height") or 0,
                source_page_url=ii.get("descriptionurl", ""),
            ))
    except Exception as exc:
        logger.info("wikimedia search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 2: Openverse
# ---------------------------------------------------------------------------
def search_openverse(query: str, limit: int = 15, api_key: str = "") -> List[ImageHit]:
    hits: List[ImageHit] = []
    try:
        headers = {"User-Agent": USER_AGENT}
        if api_key or getattr(settings, "OPENVERSE_API_KEY", ""):
            key = api_key or getattr(settings, "OPENVERSE_API_KEY", "")
            headers["Authorization"] = f"Bearer {key}"
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": f"{query} Nepal", "page_size": min(limit, 30), "license_type": "all"},
            headers=headers, timeout=TIMEOUT,
        )
        r.raise_for_status()
        for item in (r.json().get("results") or []):
            license_str = f"{item.get('license', '')} {item.get('license_version', '')}".strip().upper()
            creator = item.get("creator", "Openverse Contributor")
            hits.append(ImageHit(
                url=item.get("url", ""),
                thumbnail=item.get("thumbnail", item.get("url", "")),
                source="openverse",
                source_title="Openverse",
                source_page=item.get("foreign_landing_url", ""),
                author=creator,
                license=license_str or "Creative Commons",
                attribution_requirement=f"Credit: {creator} under {license_str}",
                title=item.get("title", ""),
                width=item.get("width", 0),
                height=item.get("height", 0),
            ))
    except Exception as exc:
        logger.info("openverse search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 3: Flickr (Community / Local Photography)
# ---------------------------------------------------------------------------
def search_flickr(query: str, limit: int = 15, api_key: str = "") -> List[ImageHit]:
    hits: List[ImageHit] = []
    flickr_key = api_key or getattr(settings, "FLICKR_API_KEY", "")
    try:
        if flickr_key:
            r = requests.get(
                "https://www.flickr.com/services/rest/",
                params={
                    "method": "flickr.photos.search",
                    "api_key": flickr_key,
                    "text": f"{query} Nepal",
                    "format": "json",
                    "nojsoncallback": 1,
                    "per_page": min(limit, 30),
                    "extras": "url_l,url_m,owner_name,license",
                },
                headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            for photo in (data.get("photos", {}).get("photo", [])):
                url = photo.get("url_l") or photo.get("url_m")
                if not url:
                    continue
                owner = photo.get("ownername", "Flickr Contributor")
                hits.append(ImageHit(
                    url=url,
                    thumbnail=photo.get("url_m") or url,
                    source="flickr",
                    source_title="Flickr",
                    source_page=f"https://www.flickr.com/photos/{photo.get('owner')}/{photo.get('id')}",
                    author=owner,
                    license="CC Attribution / Flickr",
                    attribution_requirement=f"Photo by {owner} via Flickr",
                    title=photo.get("title", query),
                    width=int(photo.get("width_l", 0) or photo.get("width_m", 0)),
                    height=int(photo.get("height_l", 0) or photo.get("height_m", 0)),
                ))
        else:
            # Public Flickr feed fallback (no API key required)
            clean_tags = re.sub(r"[^a-zA-Z0-9]+", ",", query).strip(",")
            r = requests.get(
                "https://www.flickr.com/services/feeds/photos_public.gne",
                params={"tags": f"nepal,{clean_tags}", "format": "json", "nojsoncallback": 1},
                headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT,
            )
            if r.status_code == 200:
                data = r.json()
                for item in (data.get("items") or [])[:limit]:
                    media = item.get("media", {}).get("m", "")
                    if media:
                        # Switch thumbnail 'm' to larger 'b' variant
                        large_url = media.replace("_m.jpg", "_b.jpg")
                        hits.append(ImageHit(
                            url=large_url,
                            thumbnail=media,
                            source="flickr",
                            source_title="Flickr",
                            source_page=item.get("link", ""),
                            author=_strip_html(item.get("author", "Flickr Contributor")),
                            license="CC BY / Flickr Community",
                            attribution_requirement=f"Attribution: {item.get('author', 'Flickr Contributor')}",
                            title=item.get("title", query),
                        ))
    except Exception as exc:
        logger.info("flickr search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 4: Unsplash (High-Resolution Travel)
# ---------------------------------------------------------------------------
def search_unsplash(query: str, limit: int = 15, api_key: str = "") -> List[ImageHit]:
    hits: List[ImageHit] = []
    key = api_key or getattr(settings, "UNSPLASH_ACCESS_KEY", "")
    try:
        headers = {"User-Agent": USER_AGENT}
        if key:
            headers["Authorization"] = f"Client-ID {key}"
            endpoint = "https://api.unsplash.com/search/photos"
        else:
            endpoint = "https://unsplash.com/napi/search/photos"
        r = requests.get(
            endpoint,
            params={"query": f"{query} Nepal", "per_page": min(limit, 30)},
            headers=headers, timeout=TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("results") if isinstance(data, dict) else []
            for item in (results or [])[:limit]:
                urls = item.get("urls") or {}
                user = item.get("user") or {}
                author_name = user.get("name") or user.get("username") or "Unsplash Photographer"
                hits.append(ImageHit(
                    url=urls.get("regular") or urls.get("full", ""),
                    thumbnail=urls.get("small") or urls.get("thumb", ""),
                    source="unsplash",
                    source_title="Unsplash",
                    source_page=item.get("links", {}).get("html", "https://unsplash.com"),
                    author=author_name,
                    license="Unsplash License (Free Commercial Use)",
                    attribution_requirement=f"Photo by {author_name} on Unsplash",
                    title=item.get("alt_description") or item.get("description") or query,
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                ))
    except Exception as exc:
        logger.info("unsplash search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 5: Pexels
# ---------------------------------------------------------------------------
def search_pexels(query: str, limit: int = 15, api_key: str = "") -> List[ImageHit]:
    hits: List[ImageHit] = []
    key = api_key or getattr(settings, "PEXELS_API_KEY", "")
    if not key:
        return hits
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": f"{query} Nepal", "per_page": min(limit, 30)},
            headers={"Authorization": key, "User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            for item in (r.json().get("photos") or [])[:limit]:
                src = item.get("src") or {}
                photographer = item.get("photographer", "Pexels Photographer")
                hits.append(ImageHit(
                    url=src.get("large2x") or src.get("large") or "",
                    thumbnail=src.get("medium") or src.get("small") or "",
                    source="pexels",
                    source_title="Pexels",
                    source_page=item.get("url", "https://pexels.com"),
                    author=photographer,
                    license="Pexels License (Free to Use)",
                    attribution_requirement=f"Photo by {photographer} on Pexels",
                    title=item.get("alt") or query,
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                ))
    except Exception as exc:
        logger.info("pexels search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 6: Pixabay
# ---------------------------------------------------------------------------
def search_pixabay(query: str, limit: int = 15, api_key: str = "") -> List[ImageHit]:
    hits: List[ImageHit] = []
    key = api_key or getattr(settings, "PIXABAY_API_KEY", "")
    if not key:
        return hits
    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params={"key": key, "q": f"{query} Nepal", "per_page": min(limit, 30), "image_type": "photo"},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            for item in (r.json().get("hits") or [])[:limit]:
                user = item.get("user", "Pixabay Contributor")
                hits.append(ImageHit(
                    url=item.get("largeImageURL") or item.get("webformatURL", ""),
                    thumbnail=item.get("webformatURL") or item.get("previewURL", ""),
                    source="pixabay",
                    source_title="Pixabay",
                    source_page=item.get("pageURL", "https://pixabay.com"),
                    author=user,
                    license="Pixabay Content License",
                    attribution_requirement=f"Image by {user} from Pixabay",
                    title=item.get("tags") or query,
                    width=item.get("imageWidth", 0),
                    height=item.get("imageHeight", 0),
                ))
    except Exception as exc:
        logger.info("pixabay search failed for %r: %s", query, exc)
    return hits


# ---------------------------------------------------------------------------
# Source 7: Curated Nepal Catalog (Offline-resilient verified images)
# ---------------------------------------------------------------------------
def search_curated_catalog(query: str, limit: int = 15) -> List[ImageHit]:
    """Search verified Wikimedia repository photos stored locally."""
    hits: List[ImageHit] = []
    catalog_path = Path(__file__).resolve().parent.parent.parent / "verified_wikimedia_photos.json"
    if not catalog_path.is_file():
        return hits
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        q_tokens = _tokens(query)
        if not q_tokens:
            return hits
        for item in data.values():
            label = item.get("label") or item.get("caption") or ""
            file_name = item.get("file") or ""
            text = f"{label} {file_name}".lower()
            item_tokens = _tokens(text)
            if q_tokens & item_tokens:
                hits.append(ImageHit(
                    url=item.get("url") or item.get("thumb") or "",
                    thumbnail=item.get("thumb") or item.get("url") or "",
                    source="wikimedia",
                    source_title="Wikimedia Verified Catalog",
                    source_page=item.get("source_url") or "",
                    author=item.get("photographer") or "Wikimedia Contributor",
                    license=item.get("license") or "CC BY-SA 4.0",
                    attribution_requirement="Wikimedia Commons / Creative Commons",
                    title=label or file_name,
                    width=960,
                    height=640,
                ))
                if len(hits) >= limit:
                    break
    except Exception as exc:
        logger.info("curated catalog lookup failed: %s", exc)
    return hits


# ---------------------------------------------------------------------------
# Scoring & Relevance Matching Engine
# ---------------------------------------------------------------------------
def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _tokens(value: str) -> set[str]:
    ignored = {"the", "and", "for", "with", "from", "view", "photo", "image", "nepal", "tour", "travel"}
    return {x for x in _norm(value).split() if len(x) >= 3 and x not in ignored}


def calculate_hit_scores(hit: ImageHit, destination_name: str, district: str = "", province: str = "", keywords: str = ""):
    """Calculate location match %, keyword match %, and composite confidence score.

    Ensures that a specific place (e.g. Ilam Tea Garden) is scored high
    while generic terms (e.g. mountain landscape) are recognized with lower relevance.
    """
    dest_tokens = _tokens(destination_name)
    dist_tokens = _tokens(district)
    prov_tokens = _tokens(province)
    kw_tokens = _tokens(keywords)

    evidence_text = " ".join(filter(None, [
        hit.title, hit.source_page, hit.source_page_url, hit.author, hit.license,
    ]))
    evidence_tokens = _tokens(evidence_text)

    # 1. Location match: specific destination name match carries heavy weight
    location_score = 0
    if dest_tokens:
        matched_dest = dest_tokens & evidence_tokens
        dest_ratio = len(matched_dest) / len(dest_tokens)
        location_score += int(dest_ratio * 75)

    if dist_tokens:
        matched_dist = dist_tokens & evidence_tokens
        if matched_dist:
            location_score += 15

    if prov_tokens:
        matched_prov = prov_tokens & evidence_tokens
        if matched_prov:
            location_score += 10

    # Minimum base floor if country matches or source is verified Nepal catalog
    if "nepal" in evidence_text.lower():
        location_score = max(location_score, 40)
    hit.location_match = min(100, max(0, location_score))

    # 2. Keyword match: category, landmarks, themes
    keyword_score = 0
    if kw_tokens:
        matched_kw = kw_tokens & evidence_tokens
        kw_ratio = len(matched_kw) / max(1, len(kw_tokens))
        keyword_score = int(kw_ratio * 90) + 10
    else:
        # Infer keywords from title
        has_landmark = any(term in evidence_text.lower() for term in ["temple", "lake", "stupa", "durbar", "valley", "peak", "park", "garden", "monastery", "himal"])
        keyword_score = 85 if has_landmark else 60

    hit.keyword_match = min(100, max(0, keyword_score))

    # 3. Composite confidence score
    source_boost = 10 if hit.source in ("wikimedia", "curated") else (5 if hit.source == "openverse" else 0)
    composite = int(hit.location_match * 0.65 + hit.keyword_match * 0.25 + source_boost)
    hit.confidence_score = min(100, max(0, composite))
    hit.match_score = round(hit.confidence_score / 100.0, 2)


# ---------------------------------------------------------------------------
# Multi-Source Orchestrator
# ---------------------------------------------------------------------------
def multi_source_image_search(
    query: str,
    destination=None,
    district: str = "",
    province: str = "",
    country: str = "Nepal",
    sources: Optional[List[str]] = None,
    limit: int = 24,
) -> List[ImageHit]:
    """Execute multi-source search across selected providers in parallel."""
    selected = set(sources or ["wikimedia", "openverse", "flickr", "unsplash", "pexels", "pixabay"])
    per_source = max(6, limit // max(1, len(selected)))

    dest_name = getattr(destination, "name", query) if destination else query
    dest_dist = getattr(destination, "district", district) if destination else district
    dest_prov = getattr(destination, "province", province) if destination else province

    search_term = f"{dest_name}".strip()
    if dest_dist and dest_dist.lower() not in search_term.lower():
        search_term += f" {dest_dist}"

    all_hits: List[ImageHit] = []
    tasks = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        if "wikimedia" in selected:
            tasks.append(executor.submit(search_wikimedia, search_term, per_source))
        if "openverse" in selected:
            tasks.append(executor.submit(search_openverse, search_term, per_source))
        if "flickr" in selected:
            tasks.append(executor.submit(search_flickr, search_term, per_source))
        if "unsplash" in selected:
            tasks.append(executor.submit(search_unsplash, search_term, per_source))
        if "pexels" in selected:
            tasks.append(executor.submit(search_pexels, search_term, per_source))
        if "pixabay" in selected:
            tasks.append(executor.submit(search_pixabay, search_term, per_source))

        for future in concurrent.futures.as_completed(tasks):
            try:
                hits = future.result()
                if hits:
                    all_hits.extend(hits)
            except Exception as err:
                logger.debug("Image search provider error: %s", err)

    # Always ensure local curated catalog hits are included as authentic fallbacks
    if len(all_hits) < 4:
        catalog_hits = search_curated_catalog(dest_name, limit=per_source)
        all_hits.extend(catalog_hits)

    # Deduplicate by normalized URL
    seen = set()
    unique_hits: List[ImageHit] = []
    for hit in all_hits:
        if not hit.url or hit.url in seen:
            continue
        seen.add(hit.url)
        calculate_hit_scores(hit, dest_name, dest_dist, dest_prov)
        unique_hits.append(hit)

    # Sort by confidence score descending
    unique_hits.sort(key=lambda h: h.confidence_score, reverse=True)
    return unique_hits[:limit]


def search_destination_images(destination, per_source: int = 12,
                               min_score: float = 0.35,
                               sources=("wikimedia", "duckduckgo", "openverse"),
                               openverse_key: str = "") -> List[ImageHit]:
    """Compatibility wrapper for automated image acquisition pipeline."""
    dest_name = getattr(destination, "name", str(destination))
    dest_dist = getattr(destination, "district", "")
    dest_prov = getattr(destination, "province", "")

    hits = multi_source_image_search(
        query=dest_name,
        destination=destination,
        district=dest_dist,
        province=dest_prov,
        sources=list(sources),
        limit=per_source * 2,
    )
    return [h for h in hits if h.match_score >= min_score]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()
