"""
media_app/engine.py -- moved from tourist/image_pipeline.py, same app split
rationale as translation/engine.py. Logic unchanged.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

USER_AGENT = "TourismApp/1.0 (https://github.com/Diwash234/Tourism)"

# Words that mean a result is almost certainly NOT a place photo -- this
# is the concrete fix for "Ruru Kshetra returning a girl's portrait":
# reject anything whose title/tags/description are dominated by these,
# regardless of which source returned it.
REJECT_KEYWORDS = {
    "portrait", "selfie", "headshot", "model", "fashion", "makeup",
    "wedding dress", "studio shoot", "person smiling", "close-up of face",
}


def _looks_like_a_place(text, query):
    """
    Cheap but real relevance check -- catches the specific failure mode
    reported (a person/portrait photo matching a place-name text search
    on a stock site). Two checks:
    1. None of the reject keywords appear in the source's own title/tags.
    2. At least one significant word from the query appears in the
       result's own text -- guards against a source returning its most
       "popular" unrelated photo when it has no real match.
    """
    text_lower = (text or "").lower()
    if any(bad in text_lower for bad in REJECT_KEYWORDS):
        return False

    query_words = [w for w in query.lower().split() if len(w) > 3]
    if query_words and not any(w in text_lower for w in query_words):
        return False
    return True


def _fetch_unsplash(query):
    if not settings.UNSPLASH_ACCESS_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 3},
            headers={"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"},
            timeout=6,
        )
        resp.raise_for_status()
        for result in resp.json().get("results", []):
            text = " ".join(filter(None, [result.get("description"), result.get("alt_description")]))
            if _looks_like_a_place(text, query):
                return {
                    "url": result["urls"]["regular"],
                    "thumbnail_url": result["urls"]["small"],
                    "attribution": f"Photo by {result['user']['name']} on Unsplash",
                    "source": "unsplash",
                    "source_link": result["links"]["html"],
                }
    except (requests.RequestException, KeyError) as exc:
        logger.warning("Unsplash lookup failed for %r: %s", query, exc)
    return None


def _fetch_pexels(query):
    if not settings.PEXELS_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 3},
            headers={"Authorization": settings.PEXELS_API_KEY},
            timeout=6,
        )
        resp.raise_for_status()
        for photo in resp.json().get("photos", []):
            text = photo.get("alt", "")
            if _looks_like_a_place(text, query):
                return {
                    "url": photo["src"]["large"],
                    "thumbnail_url": photo["src"]["medium"],
                    "attribution": f"Photo by {photo['photographer']} on Pexels",
                    "source": "pexels",
                    "source_link": photo["url"],
                }
    except (requests.RequestException, KeyError) as exc:
        logger.warning("Pexels lookup failed for %r: %s", query, exc)
    return None


def _fetch_pixabay(query):
    if not settings.PIXABAY_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://pixabay.com/api/",
            params={"key": settings.PIXABAY_API_KEY, "q": query, "image_type": "photo", "per_page": 3},
            timeout=6,
        )
        resp.raise_for_status()
        for hit in resp.json().get("hits", []):
            text = hit.get("tags", "")
            if _looks_like_a_place(text, query):
                return {
                    "url": hit["largeImageURL"],
                    "thumbnail_url": hit["webformatURL"],
                    "attribution": f"Photo by {hit['user']} on Pixabay",
                    "source": "pixabay",
                    "source_link": hit["pageURL"],
                }
    except (requests.RequestException, KeyError) as exc:
        logger.warning("Pixabay lookup failed for %r: %s", query, exc)
    return None


def _fetch_openverse(query):
    """No API key required -- CC-licensed image search."""
    try:
        resp = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "page_size": 3, "license_type": "commercial,modification"},
            headers={"User-Agent": USER_AGENT},
            timeout=6,
        )
        resp.raise_for_status()
        for result in resp.json().get("results", []):
            text = result.get("title", "")
            if _looks_like_a_place(text, query):
                return {
                    "url": result["url"],
                    "thumbnail_url": result.get("thumbnail", result["url"]),
                    "attribution": f"{result.get('title', 'Image')} by {result.get('creator', 'Unknown')} "
                                    f"({result.get('license', '').upper()}, via Openverse)",
                    "source": "openverse",
                    "source_link": result.get("foreign_landing_url", result["url"]),
                }
    except (requests.RequestException, KeyError) as exc:
        logger.warning("Openverse lookup failed for %r: %s", query, exc)
    return None


def _fetch_wikimedia(query):
    """No API key required."""
    try:
        search = requests.get(
            settings.WIKIMEDIA_API_URL,
            params={"action": "query", "list": "search", "srsearch": f"{query} filetype:bitmap",
                    "srnamespace": 6, "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=6,
        )
        search.raise_for_status()
        hits = search.json().get("query", {}).get("search", [])
        for hit in hits[:3]:
            title = hit["title"]
            if not _looks_like_a_place(title, query):
                continue
            info = requests.get(
                settings.WIKIMEDIA_API_URL,
                params={"action": "query", "titles": title, "prop": "imageinfo",
                        "iiprop": "url|extmetadata", "format": "json"},
                headers={"User-Agent": USER_AGENT},
                timeout=6,
            ).json()
            page = next(iter(info.get("query", {}).get("pages", {}).values()), {})
            image_info = (page.get("imageinfo") or [{}])[0]
            if image_info.get("url"):
                artist = image_info.get("extmetadata", {}).get("Artist", {}).get("value", "Wikimedia Commons contributor")
                return {
                    "url": image_info["url"],
                    "thumbnail_url": image_info["url"],
                    "attribution": f"Photo: {artist} (Wikimedia Commons)",
                    "source": "wikimedia",
                    "source_link": f"https://commons.wikimedia.org/wiki/{title}",
                }
    except (requests.RequestException, KeyError, StopIteration) as exc:
        logger.warning("Wikimedia lookup failed for %r: %s", query, exc)
    return None


# Order matters: paid/higher-quality sources first, free/keyless sources
# as fallback. Each function already returns None on no-match or error,
# never raises -- the chain just moves to the next source.
SOURCE_CHAIN = [_fetch_unsplash, _fetch_pexels, _fetch_pixabay, _fetch_openverse, _fetch_wikimedia]


def resolve_place_image(name, context="Nepal"):
    """
    The single entry point everything else should call -- destinations,
    hotels, districts, anything that needs a verified place photo.
    `context` defaults to "Nepal" to bias search results toward the
    right country. Returns None if nothing relevant was found anywhere,
    rather than a generic filler image -- callers decide their own
    placeholder policy.
    """
    query = f"{name} {context}".strip()
    for source_fn in SOURCE_CHAIN:
        result = source_fn(query)
        if result:
            return result
    return None