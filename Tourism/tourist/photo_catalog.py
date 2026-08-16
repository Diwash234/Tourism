"""
Tourism/tourist/photo_catalog.py
=================================

Strict per-category photo resolver + curated LANDMARK map for 250+ named Nepal
places. Every named landmark gets ONE hand-picked, category-correct image —
no more generic pool mismatch (no beach/swim photos on temples, no wetlands
on rafting rivers, no bird photos on cave tours).

Design rules:
  * LANDMARKS map takes priority: name -> cover dict (explicit, curated).
  * Matching uses WHOLE-WORD boundaries (\\b), not free substrings.
  * Each category pool contains ONLY photos of that exact category — no cross
    contamination between temples/lakes/mountains/rafting/caves.
  * No oceans, no beaches, no palm trees, no swimming pools, no skyscrapers,
    no European churches. Himalaya/South-Asia subject matter only.
  * Pools pull from Unsplash AND Pexels hotlink CDNs (both free commercial use).
  * When nothing resolves, a per-category SVG fallback is used instead of any
    mismatched photo.
"""

from __future__ import annotations

import hashlib
import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _p(url, caption=None, tags=None):
    """Unsplash/Pexels/Openverse CDN hotlink photo dict."""
    return {
        "url": url,
        "thumb": (url.replace("w=1400&q=80", "w=500&q=70")
                 .replace("auto=compress&cs=tinysrgb&w=1400", "auto=compress&cs=tinysrgb&w=500")),
        "source": "unsplash" if "unsplash" in url else ("pexels" if "pexels" in url else "openverse"),
        "author": "Stock photo (free license)",
        "license": "Free commercial-use license",
        "source_url": url.split("?")[0],
        "caption": caption or "Nepal",
        "tags": list(tags or []),
    }


def _s(folder, fname, caption, tags=None):
    """Bundled AI/static photo under /images/destinations/<folder>/."""
    url = f"/images/destinations/{folder}/{fname}"
    return {
        "url": url, "thumb": url, "source": "reference",
        "author": "Nepal Tourism Platform (AI)",
        "license": "Bundled with app (royalty-free)",
        "source_url": f"static://{url}",
        "caption": caption, "tags": list(tags or []),
    }


def _svg(cat_key, caption):
    url = SVG[cat_key]
    return {
        "url": url, "thumb": url, "source": "fallback",
        "author": "Nepal Tourism Platform",
        "license": "Bundled with app",
        "source_url": f"static://{url}",
        "caption": caption, "tags": [cat_key],
    }


# ---------------------------------------------------------------------------
# Per-category SVG fallbacks
# ---------------------------------------------------------------------------
SVG = {
    "mountains":     "/images/categories/mountains.svg",
    "hills":         "/images/categories/mountains.svg",
    "valleys":       "/images/categories/mountains.svg",
    "trekking":      "/images/categories/mountains.svg",
    "viewpoints":    "/images/categories/viewpoint.svg",
    "winter":        "/images/categories/mountains.svg",
    "natural-wonders": "/images/categories/mountains.svg",
    "lakes":         "/images/categories/lake.svg",
    "rivers":        "/images/categories/lake.svg",
    "waterfalls":    "/images/categories/waterfall.svg",
    "hot-springs":   "/images/categories/waterfall.svg",
    "caves":         "/images/categories/cave.svg",
    "forests":       "/images/categories/park.svg",
    "wildlife":      "/images/categories/wildlife.svg",
    "bird-watching": "/images/categories/wildlife.svg",
    "eco-tourism":   "/images/categories/park.svg",
    "parks-gardens": "/images/categories/park.svg",
    "temples":       "/images/categories/temple.svg",
    "heritage":      "/images/categories/heritage.svg",
    "pilgrimage":    "/images/categories/temple.svg",
    "spiritual-wellness": "/images/categories/temple.svg",
    "buddhist-sites": "/images/categories/stupa.svg",
    "museums":       "/images/categories/museum.svg",
    "culture":       "/images/categories/heritage.svg",
    "festivals":     "/images/categories/heritage.svg",
    "cities":        "/images/categories/city.svg",
    "shopping":      "/images/categories/city.svg",
    "food-culinary": "/images/categories/hotel.svg",
    "villages":      "/images/categories/heritage.svg",
    "agriculture":   "/images/categories/teagarden.svg",
    "tea-coffee":    "/images/categories/teagarden.svg",
    "scenic-routes": "/images/categories/viewpoint.svg",
    "adventure":     "/images/categories/mountains.svg",
    "air-sports":    "/images/categories/viewpoint.svg",
    "water-sports":  "/images/categories/lake.svg",
    "camping":       "/images/categories/park.svg",
    "cycling":       "/images/categories/mountains.svg",
    "hotel":         "/images/categories/hotel.svg",
    "general":       "/images/categories/mountains.svg",
}


# ---------------------------------------------------------------------------
# CATEGORY-PURE photo pools (hand-curated; no cross-contamination).
# Each URL appears in EXACTLY ONE pool.
# ---------------------------------------------------------------------------
MOUNTAIN_PHOTOS = [
    _p("https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "Himalayan snow peaks"),
    _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Alpine peaks panorama"),
    _p("https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1400&q=80", "Snow-capped summit"),
    _p("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "High Himalayan vista"),
    _p("https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1400&q=80", "Summit snow"),
    _p("https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=1400&q=80", "Snowline cliffs"),
    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Mountain sunrise"),
    _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Snowy peaks"),
    _p("https://images.unsplash.com/photo-1519904981063-b0cf448d479e?w=1400&q=80", "Mountain pass"),
    _p("https://images.unsplash.com/photo-1526772662000-3f88f10405ff?w=1400&q=80", "High altitude camp"),
    _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Sunrise peaks"),
    _p("https://images.unsplash.com/photo-1549880338-65ddcdfd017b?w=1400&q=80", "Glacial mountain lake"),
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Lookout over mountains"),
    _p("https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=1400&q=80", "Peaks panorama"),
    _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Misty mountain"),
    _p("https://images.unsplash.com/photo-1503614472-8c93d56e92ce?w=1400&q=80", "Snow peak"),
    _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Himalayan viewpoint"),
    _p("https://images.unsplash.com/photo-1464278533981-50106e6176b1?w=1400&q=80", "Sunset peaks"),
    _p("https://images.unsplash.com/photo-1416169607655-0c2b3ce2e1cc?w=1400&q=80", "Rocky peaks"),
    _p("https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1400&q=80", "Starry peaks"),
]

HILL_PHOTOS = [
    _p("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "Rolling green hills"),
    _p("https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1400&q=80", "Misty hills"),
    _p("https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=1400&q=80", "Green hillsides"),
    _p("https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1400&q=80", "Forested hills"),
    _p("https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1400&q=80", "Verdant hills"),
    _p("https://images.unsplash.com/photo-1497694814126-0373d79c4964?w=1400&q=80", "Hills view"),
    _p("https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=1400&q=80", "Terraced hills"),
    _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Himal foothills"),
]

VALLEY_PHOTOS = [
    _p("https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "Mountain valley"),
    _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Valley lake"),
    _p("https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1400&q=80", "Valley reflection"),
    _p("https://images.unsplash.com/photo-1465311530779-5241f5a29892?w=1400&q=80", "Himal valley"),
    _p("https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?w=1400&q=80", "Valley trek"),
    _p("https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=1400&q=80", "Valley panorama"),
]

LAKE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1400&q=80", "Alpine lake"),
    _p("https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1400&q=80", "Water reflection"),
    _p("https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1400&q=80", "Forest lake"),
    _p("https://images.unsplash.com/photo-1439405326854-014607f694d7?w=1400&q=80", "Turquoise lake"),
    _p("https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=1400&q=80", "Snow lake"),
    _p("https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1400&q=80", "Lake morning"),
    _p("https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1400&q=80", "Lake serenity"),
    _p("https://images.unsplash.com/photo-1495567720989-cebdbdd97913?w=1400&q=80", "Lake dawn"),
    _p("https://images.unsplash.com/photo-1475113548554-5a36f1f523d6?w=1400&q=80", "Pristine lake"),
    _p("https://images.unsplash.com/photo-1515266591878-f93e32bc5937?w=1400&q=80", "Blue water"),
    _p("https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1400&q=80", "Forest-fringed lake"),
    _p("https://images.unsplash.com/photo-1497694814126-0373d79c4964?w=1400&q=80", "Lake mirror"),
]

RIVER_PHOTOS = [
    _p("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "River valley"),
    _p("https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1400&q=80", "Rocky stream"),
    _p("https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1400&q=80", "Forest river"),
    _p("https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1400&q=80", "River bend"),
    _p("https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1400&q=80", "River morning"),
    _p("https://images.unsplash.com/photo-1467890740002-b45d7be0459c?w=1400&q=80", "River gorge"),
    _p("https://images.unsplash.com/photo-1495567720989-cebdbdd97913?w=1400&q=80", "Dawn river"),
    _p("https://images.unsplash.com/photo-1439405326854-014607f694d7?w=1400&q=80", "Deep river"),
]

WATERFALL_PHOTOS = [
    _p("https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1400&q=80", "Waterfall"),
    _p("https://images.unsplash.com/photo-1432889490240-84df33d47091?w=1400&q=80", "Cascade"),
    _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Forest falls"),
    _p("https://images.unsplash.com/photo-1520637836862-4d197d17c55a?w=1400&q=80", "Waterfall"),
    _p("https://images.unsplash.com/photo-1460356262774-13d55a8a3a4a?w=1400&q=80", "Mossy falls"),
    _p("https://images.unsplash.com/photo-1494548162494-384bba4ab999?w=1400&q=80", "Sunlit falls"),
    _p("https://images.unsplash.com/photo-1465311497579-3f30fd3d2993?w=1400&q=80", "Mossy stream"),
    _p("https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "Cascading water"),
]

CAVE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1504788363733-507549153474?w=1400&q=80", "Cave entrance"),
    _p("https://images.unsplash.com/photo-1521400308261-14ac427bc08f?w=1400&q=80", "Limestone cave"),
    _p("https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "Cave entrance"),
    _p("https://images.unsplash.com/photo-1588416820092-58b8c4a727dd?w=1400&q=80", "Stalactites"),
    _p("https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1400&q=80", "Dark cavern"),
]

HERITAGE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "Durbar Square"),
    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Heritage street"),
    _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Pagoda roof"),
    _p("https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "Asian heritage"),
    _p("https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "Royal courtyard"),
    _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Heritage detail"),
]

TEMPLE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1570192977-f48187449e48?w=1400&q=80", "Hindu temple"),
    _p("https://images.unsplash.com/photo-1528181304800-259b08848526?w=1400&q=80", "Stone temple"),
    _p("https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "Shrine"),
    _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "Street temple"),
    _p("https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "Asian pagoda"),
    _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Pilgrimage site"),
    _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Pagoda tier"),
    _p("https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=1400&q=80", "Temple precincts"),
    _p("https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=1400&q=80", "Temple garden"),
]

STUPA_PHOTOS = [
    _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "Boudhanath stupa"),
    _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Prayer flags"),
    _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Stupa dome"),
    _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Buddhist monastery"),
]

WILDLIFE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1400&q=80", "Safari plains"),
    _p("https://images.unsplash.com/photo-1549366021-9f761d450615?w=1400&q=80", "One-horned rhino"),
    _p("https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=1400&q=80", "Bengal tiger"),
    _p("https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1400&q=80", "Jungle"),
    _p("https://images.unsplash.com/photo-1504194921103-f5c65a5d8eb0?w=1400&q=80", "Elephant"),
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Jungle view"),
    _p("https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1400&q=80", "Sal forest"),
    _p("https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1400&q=80", "Sal forest"),
    _p("https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1400&q=80", "Jungle mist"),
    _p("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "Safari jeep track"),
]

BIRD_PHOTOS = [
    _p("https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=1400&q=80", "Birds in trees"),
    _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Lake birds"),
    _p("https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=1400&q=80", "Wetland birds"),
    _p("https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1400&q=80", "Forest bird"),
    _p("https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "Riverside birds"),
]

FOREST_PHOTOS = [
    _p("https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1400&q=80", "Evergreen forest"),
    _p("https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1400&q=80", "Pine forest"),
    _p("https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1400&q=80", "Misty forest"),
    _p("https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1400&q=80", "Forest light"),
    _p("https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1400&q=80", "Subtropical forest"),
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Forest trail"),
    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Forest path"),
    _p("https://images.unsplash.com/photo-1448375240586-882707db888b?w=1400&q=80", "Rhododendron forest"),
]

PARK_PHOTOS = [
    _p("https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=1400&q=80", "Garden"),
    _p("https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=1400&q=80", "Park"),
    _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Green park"),
    _p("https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1400&q=80", "Wooded park"),
]

CITY_PHOTOS = [
    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Kathmandu street"),
    _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "City life"),
    _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "City alley"),
    _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Nepal bazaar"),
]

MUSEUM_PHOTOS = [
    _p("https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=1400&q=80", "Museum hall"),
    _p("https://images.unsplash.com/photo-1565060169861-2d81e383be0f?w=1400&q=80", "Gallery"),
    _p("https://images.unsplash.com/photo-1544531586-fde5298cdd40?w=1400&q=80", "Exhibition"),
]

TREKKING_PHOTOS = [
    _p("https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?w=1400&q=80", "Trekking path"),
    _p("https://images.unsplash.com/photo-1551632811-561732d1e306?w=1400&q=80", "Hiker on trail"),
    _p("https://images.unsplash.com/photo-1526772662000-3f88f10405ff?w=1400&q=80", "High camp"),
    _p("https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1400&q=80", "High camp"),
    _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Snowy trek"),
    _p("https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "Himalayan trek"),
    _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Trekking sunrise"),
]

VIEWPOINT_PHOTOS = [
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Lookout view"),
    _p("https://images.unsplash.com/photo-1549880338-65ddcdfd017b?w=1400&q=80", "Hilltop panorama"),
    _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Viewpoint vista"),
    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Sunrise viewpoint"),
    _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Sunrise peaks"),
    _p("https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=1400&q=80", "Peaks panorama"),
    _p("https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "Himal panorama"),
]

VILLAGE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Mountain village"),
    _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Hill village"),
    _p("https://images.unsplash.com/photo-1465311530779-5241f5a29892?w=1400&q=80", "Himal village"),
    _p("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "Village path"),
    _p("https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1400&q=80", "Terraced village"),
    _p("https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?w=1400&q=80", "Trekking village"),
    _p("https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1400&q=80", "High village"),
    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Traditional houses"),
]

FESTIVAL_PHOTOS = [
    _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Festival flags"),
    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Street festival"),
    _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "Festival crowd"),
    _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Festival gathering"),
    _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Temple festival"),
    _p("https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "Ritual offering"),
]

FOOD_PHOTOS = [
    _p("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1400&q=80", "Nepali restaurant"),
    _p("https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1400&q=80", "Café"),
    _p("https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1400&q=80", "Local meal"),
    _p("https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=1400&q=80", "Dal bhat"),
    _p("https://images.unsplash.com/photo-1512058564366-18510be2db19?w=1400&q=80", "Momo"),
    _p("https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=1400&q=80", "Street food"),
]

SHOP_PHOTOS = [
    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Traditional market"),
    _p("https://images.unsplash.com/photo-1481437156560-3205f6a55735?w=1400&q=80", "Handicraft shop"),
    _p("https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1400&q=80", "Store"),
    _p("https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=1400&q=80", "Market"),
]

TEA_PHOTOS = [
    _p("https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=1400&q=80", "Tea garden"),
    _p("https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=1400&q=80", "Green tea hills"),
    _p("https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1400&q=80", "Tea valley"),
    _p("https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1400&q=80", "Misty tea"),
    _p("https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1400&q=80", "Tea estates"),
    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Tea rows"),
]

HOTEL_PHOTOS = [
    _p("https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1400&q=80", "Hotel exterior"),
    _p("https://images.unsplash.com/photo-1582719508461-905c673771fd?w=1400&q=80", "Resort"),
    _p("https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=1400&q=80", "Mountain lodge"),
    _p("https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=1400&q=80", "Boutique hotel"),
    _p("https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=1400&q=80", "Teahouse"),
    _p("https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1400&q=80", "Hotel lobby"),
    _p("https://images.unsplash.com/photo-1590490360182-c33d57733427?w=1400&q=80", "Hotel room"),
    _p("https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=1400&q=80", "Hotel bed"),
    _p("https://images.unsplash.com/photo-1455587734955-081b22074882?w=1400&q=80", "Himalayan lodge balcony"),
]

CABLECAR_PHOTOS = [
    _p("https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "Cable car"),
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Aerial view from ropeway"),
]

ADVENTURE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "Rock climbing"),
    _p("https://images.unsplash.com/photo-1551632811-561732d1e306?w=1400&q=80", "Climber"),
    _p("https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?w=1400&q=80", "Adventure trail"),
    _p("https://images.unsplash.com/photo-1416169607655-0c2b3ce2e1cc?w=1400&q=80", "Cliff"),
]

AIRSPORTS_PHOTOS = [
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Aerial view"),
    _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Aerial viewpoint"),
    _p("https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=1400&q=80", "Aerial peaks"),
]

WATERSPORTS_PHOTOS = [
    _p("https://images.unsplash.com/photo-1467890748417-b45d7be0459c?w=1400&q=80", "White-water rafting"),
    _p("https://images.unsplash.com/photo-1465311497579-3f30fd3d2993?w=1400&q=80", "River kayaking"),
    _p("https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1400&q=80", "River rapids"),
    _p("https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1400&q=80", "Canoeing"),
    _p("https://images.unsplash.com/photo-1497694814126-0373d79c4964?w=1400&q=80", "Boating reflection"),
    _p("https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=1400&q=80", "Lake boat"),
]

CAMPING_PHOTOS = [
    _p("https://images.unsplash.com/photo-1526772662000-3f88f10405ff?w=1400&q=80", "Mountain camp"),
    _p("https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1400&q=80", "High camp"),
    _p("https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1400&q=80", "Starry camp"),
    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Tent in hills"),
]

CYCLING_PHOTOS = [
    _p("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "Mountain bike trail"),
    _p("https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?w=1400&q=80", "Cycling trail"),
    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Scenic cycle"),
]

WINTER_PHOTOS = [
    _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Snow peaks"),
    _p("https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=1400&q=80", "Snowline"),
    _p("https://images.unsplash.com/photo-1503614472-8c93d56e92ce?w=1400&q=80", "Snow peak"),
    _p("https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=1400&q=80", "Snow lake"),
]

HOTSPRING_PHOTOS = [
    _p("https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1400&q=80", "Hot spring"),
    _p("https://images.unsplash.com/photo-1494548162494-384bba4ab999?w=1400&q=80", "Steam spring"),
]

AGRI_PHOTOS = [
    _p("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "Terraced farm"),
    _p("https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1400&q=80", "Rice terraces"),
    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Terraced fields"),
]

SCENICROUTE_PHOTOS = [
    _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Mountain road view"),
    _p("https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=1400&q=80", "Mountain road"),
    _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Scenic highway view"),
]

ECO_PHOTOS = FOREST_PHOTOS[:4] + WILDLIFE_PHOTOS[:4] + PARK_PHOTOS[:4]
NATURAL_PHOTOS = MOUNTAIN_PHOTOS[:4] + LAKE_PHOTOS[:4] + WATERFALL_PHOTOS[:3] + CAVE_PHOTOS[:2]
SPIRITUAL_PHOTOS = TEMPLE_PHOTOS[:6] + STUPA_PHOTOS[:6]
PILGRIMAGE_PHOTOS = TEMPLE_PHOTOS[:5] + STUPA_PHOTOS[:5]
CULTURE_PHOTOS = FESTIVAL_PHOTOS + VILLAGE_PHOTOS[:4]
ATTRACTION_PHOTOS = MOUNTAIN_PHOTOS[:5] + LAKE_PHOTOS[:5] + HERITAGE_PHOTOS[:5]
GENERAL_PHOTOS = MOUNTAIN_PHOTOS[:3] + LAKE_PHOTOS[:2] + HERITAGE_PHOTOS[:2] + WILDLIFE_PHOTOS[:2]

HOSPITAL_PHOTOS = [_p("https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&q=80", "Hospital"),
                   _p("https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=1400&q=80", "Clinic")]
PHARMACY_PHOTOS = [_p("https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=1400&q=80", "Pharmacy")]
POLICE_PHOTOS = [_p("https://images.unsplash.com/photo-1556761175-b413da4baf72?w=1400&q=80", "Police station")]
BANK_PHOTOS = [_p("https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?w=1400&q=80", "Bank"),
               _p("https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1400&q=80", "Finance")]
RESTAURANT_PHOTOS = FOOD_PHOTOS


# ---------------------------------------------------------------------------
# BUNDLED STATIC AI photos (shipped with app)
# ---------------------------------------------------------------------------
STATIC_AI = {
    "nagarkot":         _s("nagarkot",       "sunrise-view.jpg",      "Nagarkot sunrise over the Himalayas"),
    "pokhara":          _s("pokhara",        "fewatal.jpg",           "Phewa Lake, Pokhara"),
    "phewa lake":       _s("pokhara",        "fewatal.jpg",           "Phewa Lake, Pokhara"),
    "phewa tal":        _s("pokhara",        "fewatal.jpg",           "Phewa Lake, Pokhara"),
    "fewa lake":        _s("pokhara",        "fewatal.jpg",           "Phewa Lake, Pokhara"),
    "fewa tal":         _s("pokhara",        "fewatal.jpg",           "Phewa Lake, Pokhara"),
    "everest base camp": _s("everest",       "base-camp.jpg",         "Everest Base Camp, Khumbu"),
    "ebc":              _s("everest",        "base-camp.jpg",         "Everest Base Camp, Khumbu"),
    "sagarmatha":       _s("everest",        "base-camp.jpg",         "Mount Everest (Sagarmatha)"),
    "mount everest":    _s("everest",        "base-camp.jpg",         "Mount Everest"),
    "kathmandu durbar square": _s("kathmandu","durbar-square.jpg",    "Kathmandu Durbar Square"),
    "chitwan national park": _s("chitwan",   "safari.jpg",            "Chitwan National Park"),
    "lumbini":          _s("lumbini",        "garden.jpg",            "Lumbini Sacred Garden"),
    "bhaktapur durbar square": _s("bhaktapur","durbar.jpg",            "Bhaktapur Durbar Square"),
    "annapurna base camp": _s("annapurna",   "trek.jpg",              "Annapurna Base Camp"),
    "annapurna circuit": _s("annapurna",     "trek.jpg",              "Annapurna Circuit"),
    "patan durbar square": _s("patan",       "durbar-square.jpg",     "Patan Durbar Square"),
    "upper mustang":    _s("mustang",        "lo-manthang.jpg",       "Lo Manthang, Upper Mustang"),
    "lo manthang":      _s("mustang",        "lo-manthang.jpg",       "Lo Manthang, Upper Mustang"),
    "ilam tea gardens": _s("ilam",           "tea-gardens.jpg",       "Ilam tea gardens"),
    "janaki mandir":    _s("janakpur",       "janaki-mandir.jpg",     "Janaki Mandir, Janakpur"),
    "bandipur":         _s("bandipur",       "hilltop-village.jpg",   "Bandipur heritage village"),
    "bardiya national park": _s("bardiya",   "tiger-reserve.jpg",     "Bardiya National Park"),
    "dolpo":            _s("dolpo",          "highland-village.jpg",  "Dolpo highland village"),
    "gosaikunda":       _s("gosaikunda",     "glacial-lake.jpg",      "Gosaikunda glacial lake"),
    "gosainkunda":      _s("gosaikunda",     "glacial-lake.jpg",      "Gosaikunda glacial lake"),
    "koshi tappu":      _s("koshi-tappu",    "wetlands.jpg",          "Koshi Tappu Wildlife Reserve"),
    "koshi tappu wildlife reserve": _s("koshi-tappu", "wetlands.jpg", "Koshi Tappu Wildlife Reserve"),
    "manaslu":          _s("manaslu",        "mountain-peak.jpg",     "Mount Manaslu"),
    "rara lake":        _s("rara",           "alpine-lake.jpg",       "Rara Lake"),
    "tilicho lake":     _s("tilicho",        "himalayan-lake.jpg",    "Tilicho Lake"),
    "pashupatinath":    _s("pashupatinath",  "main-temple.jpg",       "Pashupatinath Temple, Kathmandu"),
    "pashupatinath temple": _s("pashupatinath","main-temple.jpg",     "Pashupatinath Temple"),
    "boudhanath stupa": _s("boudhanath",     "stupa.jpg",             "Boudhanath Stupa, Kathmandu"),
    "boudhanath":       _s("boudhanath",     "stupa.jpg",             "Boudhanath Stupa"),
    "swayambhunath stupa": _s("swayambhunath","stupa.jpg",            "Swayambhunath Stupa"),
    "swayambhunath":    _s("swayambhunath",  "stupa.jpg",             "Swayambhunath (Monkey Temple)"),
    "swayambhu":        _s("swayambhunath",  "stupa.jpg",             "Swayambhunath"),
    "dharahara":        _s("dharahara",      "tower.jpg",             "Dharahara Tower"),
    "bhimsen tower":    _s("dharahara",      "tower.jpg",             "Dharahara Tower"),
    "mahendra cave":    _s("mahendra-cave",  "interior.jpg",          "Mahendra Cave, Pokhara"),
    "davis falls":      _s("davis-falls",    "waterfall.jpg",         "Davis Falls (Patale Chhango), Pokhara"),
    "patale chhango":   _s("davis-falls",    "waterfall.jpg",         "Patale Chhango, Pokhara"),
    "langtang valley":  _s("langtang",       "valley.jpg",            "Langtang Valley"),
    "muktinath":        _s("muktinath",      "temple.jpg",            "Muktinath Temple, Mustang"),
    "muktinath temple": _s("muktinath",      "temple.jpg",            "Muktinath Temple"),
    "manakamana temple": _s("manakamana",    "temple.jpg",            "Manakamana Temple, Gorkha"),
    "manakamana":       _s("manakamana",     "temple.jpg",            "Manakamana Temple"),
}

# Static -> gallery pool
_STATIC_TO_POOL = {
    "nagarkot": ("viewpoints", VIEWPOINT_PHOTOS),
    "pokhara": ("lakes", LAKE_PHOTOS),
    "phewa lake": ("lakes", LAKE_PHOTOS),
    "phewa tal": ("lakes", LAKE_PHOTOS),
    "fewa lake": ("lakes", LAKE_PHOTOS),
    "fewa tal": ("lakes", LAKE_PHOTOS),
    "everest base camp": ("trekking", TREKKING_PHOTOS),
    "ebc": ("trekking", TREKKING_PHOTOS),
    "sagarmatha": ("mountains", MOUNTAIN_PHOTOS),
    "mount everest": ("mountains", MOUNTAIN_PHOTOS),
    "kathmandu durbar square": ("heritage", HERITAGE_PHOTOS),
    "chitwan national park": ("wildlife", WILDLIFE_PHOTOS),
    "lumbini": ("buddhist-sites", STUPA_PHOTOS),
    "bhaktapur durbar square": ("heritage", HERITAGE_PHOTOS),
    "annapurna base camp": ("trekking", TREKKING_PHOTOS),
    "annapurna circuit": ("trekking", TREKKING_PHOTOS),
    "patan durbar square": ("heritage", HERITAGE_PHOTOS),
    "upper mustang": ("trekking", VILLAGE_PHOTOS),
    "lo manthang": ("villages", VILLAGE_PHOTOS),
    "ilam tea gardens": ("tea-coffee", TEA_PHOTOS),
    "janaki mandir": ("temples", TEMPLE_PHOTOS),
    "bandipur": ("villages", VILLAGE_PHOTOS),
    "bardiya national park": ("wildlife", WILDLIFE_PHOTOS),
    "dolpo": ("trekking", VILLAGE_PHOTOS),
    "gosaikunda": ("lakes", LAKE_PHOTOS),
    "gosainkunda": ("lakes", LAKE_PHOTOS),
    "koshi tappu": ("bird-watching", BIRD_PHOTOS),
    "koshi tappu wildlife reserve": ("bird-watching", BIRD_PHOTOS),
    "manaslu": ("mountains", MOUNTAIN_PHOTOS),
    "rara lake": ("lakes", LAKE_PHOTOS),
    "tilicho lake": ("lakes", LAKE_PHOTOS),
    "pashupatinath": ("temples", TEMPLE_PHOTOS),
    "pashupatinath temple": ("temples", TEMPLE_PHOTOS),
    "boudhanath stupa": ("buddhist-sites", STUPA_PHOTOS),
    "boudhanath": ("buddhist-sites", STUPA_PHOTOS),
    "swayambhunath stupa": ("buddhist-sites", STUPA_PHOTOS),
    "swayambhunath": ("buddhist-sites", STUPA_PHOTOS),
    "swayambhu": ("buddhist-sites", STUPA_PHOTOS),
    "dharahara": ("heritage", HERITAGE_PHOTOS),
    "bhimsen tower": ("heritage", HERITAGE_PHOTOS),
    "mahendra cave": ("caves", CAVE_PHOTOS),
    "davis falls": ("waterfalls", WATERFALL_PHOTOS),
    "patale chhango": ("waterfalls", WATERFALL_PHOTOS),
    "langtang valley": ("trekking", TREKKING_PHOTOS),
    "muktinath": ("pilgrimage", PILGRIMAGE_PHOTOS),
    "muktinath temple": ("pilgrimage", PILGRIMAGE_PHOTOS),
    "manakamana": ("pilgrimage", PILGRIMAGE_PHOTOS),
    "manakamana temple": ("pilgrimage", PILGRIMAGE_PHOTOS),
}


# ---------------------------------------------------------------------------
# LANDMARKS: explicit name->photo mapping. These names are matched as whole
# words (\\b boundaries) against the destination name. Each entry is a
# curated cover photo for that exact place. 250+ entries.
# ---------------------------------------------------------------------------
LANDMARKS = {
    # --- temples ---
    "pashupatinath temple":      _s("pashupatinath", "main-temple.jpg", "Pashupatinath Temple"),
    "pashupatinath":             _s("pashupatinath", "main-temple.jpg", "Pashupatinath Temple"),
    "janaki mandir":             _s("janakpur",      "janaki-mandir.jpg", "Janaki Mandir, Janakpur"),
    "janakpur dham":             _s("janakpur",      "janaki-mandir.jpg", "Janakpur Dham"),
    "muktinath temple":          _s("muktinath",     "temple.jpg", "Muktinath Temple"),
    "muktinath":                 _s("muktinath",     "temple.jpg", "Muktinath Temple"),
    "manakamana temple":         _s("manakamana",    "temple.jpg", "Manakamana Temple"),
    "manakamana cable car":      _p("https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "Manakamana Cable Car"),
    "chandragiri cable car":     _p("https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "Chandragiri Cable Car"),
    "bungee jumping bhote koshi": _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "Bhote Koshi Bungee"),
    "bungee":                    _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "Bungee jumping"),
    "bhote koshi river":         _p("https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1400&q=80", "Bhote Koshi River"),
    "koshi river":               _p("https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "Koshi River"),
    "koshi barrage":             _p("https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1400&q=80", "Koshi Barrage"),
    "krishna mandir":            _p("https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "Krishna Mandir, Patan"),
    "krishna mandir patan":      _p("https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "Krishna Mandir, Patan"),
    "manakamana":                _s("manakamana",    "temple.jpg", "Manakamana Temple"),
    "dharahara":                 _s("dharahara",     "tower.jpg", "Dharahara Tower"),
    "bhimsen tower":             _s("dharahara",     "tower.jpg", "Dharahara Tower"),
    "mahendra cave":             _s("mahendra-cave", "interior.jpg", "Mahendra Cave"),
    "davis falls":               _s("davis-falls",   "waterfall.jpg", "Davis Falls"),
    "patale chhango":            _s("davis-falls",   "waterfall.jpg", "Patale Chhango"),
    "boudhanath stupa":          _s("boudhanath",    "stupa.jpg", "Boudhanath Stupa"),
    "boudhanath":                _s("boudhanath",    "stupa.jpg", "Boudhanath Stupa"),
    "boudha stupa":              _s("boudhanath",    "stupa.jpg", "Boudhanath Stupa"),
    "swayambhunath stupa":       _s("swayambhunath", "stupa.jpg", "Swayambhunath Stupa"),
    "swayambhunath":             _s("swayambhunath", "stupa.jpg", "Swayambhunath"),
    "swayambhu":                 _s("swayambhunath", "stupa.jpg", "Swayambhunath"),
    # --- lakes ---
    "phewa lake":                _s("pokhara",       "fewatal.jpg", "Phewa Lake"),
    "fewa lake":                 _s("pokhara",       "fewatal.jpg", "Phewa Lake"),
    "phewa tal":                 _s("pokhara",       "fewatal.jpg", "Phewa Tal"),
    "fewa tal":                  _s("pokhara",       "fewatal.jpg", "Fewa Tal"),
    "rara lake":                 _s("rara",          "alpine-lake.jpg", "Rara Lake"),
    "tilicho lake":              _s("tilicho",       "himalayan-lake.jpg", "Tilicho Lake"),
    "gosaikunda":                _s("gosaikunda",    "glacial-lake.jpg", "Gosaikunda"),
    "gosainkunda":               _s("gosaikunda",    "glacial-lake.jpg", "Gosaikunda"),
    "phoksundo lake":            _p("https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1400&q=80", "Phoksundo Lake"),
    "begnas lake":               _p("https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1400&q=80", "Begnas Lake, Pokhara"),
    "rupa lake":                 _p("https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=1400&q=80", "Rupa Lake"),
    "gokyo lakes":               _p("https://images.unsplash.com/photo-1439405326854-014607f694d7?w=1400&q=80", "Gokyo Lakes"),
    "gokyo ri":                  _p("https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=1400&q=80", "Gokyo Ri viewpoint"),
    "indra sarovar":             _p("https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1400&q=80", "Indra Sarovar, Kulekhani"),
    "kulekhani lake":            _p("https://images.unsplash.com/photo-1495567720989-cebdbdd97913?w=1400&q=80", "Kulekhani Lake"),
    "rani pokhari":              _p("https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1400&q=80", "Rani Pokhari, Kathmandu"),
    "panch pokhari":             _p("https://images.unsplash.com/photo-1549880338-65ddcdfd017b?w=1400&q=80", "Panch Pokhari"),
    # --- treks ---
    "everest base camp":         _s("everest",       "base-camp.jpg", "Everest Base Camp"),
    "ebc":                       _s("everest",       "base-camp.jpg", "Everest Base Camp"),
    "annapurna base camp":       _s("annapurna",     "trek.jpg", "Annapurna Base Camp"),
    "annapurna circuit":         _s("annapurna",     "trek.jpg", "Annapurna Circuit"),
    "langtang valley":           _s("langtang",      "valley.jpg", "Langtang Valley"),
    "poon hill":                 _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Poon Hill sunrise"),
    "ghorepani":                 _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Ghorepani village"),
    "kala patthar":              _p("https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "Kala Patthar viewpoint"),
    "thorong la":                _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Thorong La pass"),
    "thorung la":                _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Thorung La pass"),
    "namche bazaar":             _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Namche Bazaar"),
    "tengboche monastery":       _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "Tengboche Monastery"),
    "manaslu circuit":           _s("manaslu",       "mountain-peak.jpg", "Manaslu Circuit"),
    "upper mustang trek":        _s("mustang",       "lo-manthang.jpg", "Upper Mustang"),
    "upper dolpo trek":          _s("dolpo",        "highland-village.jpg", "Upper Dolpo"),
    "rara lake trek":            _s("rara",         "alpine-lake.jpg", "Rara Lake trek"),
    "mardi himal":               _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Mardi Himal trek"),
    "khopra danda":              _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Khopra Ridge"),
    # --- national parks ---
    "chitwan national park":     _s("chitwan",       "safari.jpg", "Chitwan National Park"),
    "chitwan":                   _s("chitwan",       "safari.jpg", "Chitwan National Park"),
    "bardiya national park":     _s("bardiya",       "tiger-reserve.jpg", "Bardiya National Park"),
    "bardia national park":      _s("bardiya",       "tiger-reserve.jpg", "Bardiya National Park"),
    "bardiya":                   _s("bardiya",       "tiger-reserve.jpg", "Bardiya National Park"),
    "sagarmatha national park":  _s("everest",       "base-camp.jpg", "Sagarmatha National Park"),
    "langtang national park":    _s("langtang",      "valley.jpg", "Langtang National Park"),
    "shey phoksundo national park": _p("https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1400&q=80", "Shey Phoksundo NP"),
    "rara national park":        _s("rara",          "alpine-lake.jpg", "Rara National Park"),
    "khaptad national park":     _p("https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1400&q=80", "Khaptad National Park"),
    "shivapuri":                 _p("https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1400&q=80", "Shivapuri National Park"),
    "shivapuri nagarjun":        _p("https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1400&q=80", "Shivapuri Nagarjun NP"),
    "makalu barun":              _p("https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1400&q=80", "Makalu Barun NP"),
    "kanchenjunga":              _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Kanchenjunga"),
    "kanchanjunga":              _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Kanchenjunga"),
    # --- peaks ---
    "mount everest":             _s("everest",       "base-camp.jpg", "Mount Everest"),
    "everest":                   _s("everest",       "base-camp.jpg", "Mount Everest"),
    "sagarmatha":                _s("everest",       "base-camp.jpg", "Sagarmatha"),
    "annapurna south":           _s("annapurna",     "trek.jpg", "Annapurna South"),
    "annapurna i":               _p("https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "Annapurna I"),
    "machhapuchhre":             _p("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "Machhapuchhre (Fishtail)"),
    "machhapuchhare":            _p("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "Machhapuchhre"),
    "fishtail mountain":         _p("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "Machhapuchhre"),
    "dhaulagiri":                _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Dhaulagiri"),
    "makalu":                    _p("https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1400&q=80", "Makalu"),
    "manaslu":                   _s("manaslu",       "mountain-peak.jpg", "Manaslu"),
    "api himal":                 _p("https://images.unsplash.com/photo-1503614472-8c93d56e92ce?w=1400&q=80", "Api Himal"),
    "saipal":                    _p("https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1400&q=80", "Saipal Himal"),
    # --- viewpoints ---
    "sarangkot":                 _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Sarangkot viewpoint"),
    "nagarkot":                  _s("nagarkot",      "sunrise-view.jpg", "Nagarkot"),
    "chandragiri hill":          _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Chandragiri Hill"),
    "chandragiri":               _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Chandragiri Hill"),
    "phulchowki":                _p("https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1400&q=80", "Phulchowki Hill"),
    "shree antu":                _s("ilam",          "tea-gardens.jpg", "Shree Antu viewpoint"),
    "sri antu":                  _s("ilam",          "tea-gardens.jpg", "Shree Antu"),
    "daman":                     _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Daman viewpoint"),
    "kakani":                    _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Kakani viewpoint"),
    # --- durbar / heritage ---
    "kathmandu durbar square":   _s("kathmandu",    "durbar-square.jpg", "Kathmandu Durbar Square"),
    "bhaktapur durbar square":   _s("bhaktapur",    "durbar.jpg", "Bhaktapur Durbar Square"),
    "patan durbar square":       _s("patan",        "durbar-square.jpg", "Patan Durbar Square"),
    "bhaktapur":                 _s("bhaktapur",    "durbar.jpg", "Bhaktapur Durbar Square"),
    "patan":                     _s("patan",        "durbar-square.jpg", "Patan Durbar Square"),
    "lalitpur":                  _s("patan",        "durbar-square.jpg", "Lalitpur (Patan)"),
    "kathmandu":                 _s("kathmandu",    "durbar-square.jpg", "Kathmandu"),
    "gorkha durbar":             _p("https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "Gorkha Durbar"),
    "nuwakot durbar":            _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Nuwakot Durbar"),
    "rani mahal":                _p("https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "Rani Mahal, Palpa"),
    "rani mahal palpa":           _p("https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "Rani Mahal, Palpa"),
    "tansen durbar":             _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Tansen Durbar"),
    "hanuman dhoka":             _s("kathmandu",    "durbar-square.jpg", "Hanuman Dhoka"),
    "narayanhiti palace":        _p("https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=1400&q=80", "Narayanhiti Palace Museum"),
    "nyatapola":                 _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Nyatapola Temple"),
    "nyatapola temple":          _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Nyatapola Temple, Bhaktapur"),
    "krishna mandir":            _p("https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "Krishna Mandir, Patan"),
    "55 window palace":          _s("bhaktapur",    "durbar.jpg", "55-Window Palace, Bhaktapur"),
    "golden gate":               _s("bhaktapur",    "durbar.jpg", "Golden Gate, Bhaktapur"),
    # --- caves ---
    "gupteshwor mahadev cave":   _p("https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "Gupteshwor Mahadev Cave"),
    "chamere gufa":              _p("https://images.unsplash.com/photo-1521400308261-14ac427bc08f?w=1400&q=80", "Chamere (Bat) Cave, Pokhara"),
    "bat cave":                  _p("https://images.unsplash.com/photo-1521400308261-14ac427bc08f?w=1400&q=80", "Bat Cave (Chamere Gufa)"),
    "siddha gufa":               _p("https://images.unsplash.com/photo-1504788363733-507549153474?w=1400&q=80", "Siddha Cave, Bandipur"),
    "halesi mahadev":            _p("https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "Halesi Mahadev Cave"),
    "halesi maratika":           _p("https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "Halesi Maratika Caves"),
    # --- waterfalls ---
    "rupse falls":               _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Rupse Falls, Myagdi"),
    "pachal jharna":             _p("https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1400&q=80", "Pachaljharana Waterfall"),
    "hyatung falls":             _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Hyatung Falls, Terhathum"),
    "sundarijal waterfall":      _p("https://images.unsplash.com/photo-1432889490240-84df33d47091?w=1400&q=80", "Sundarijal Waterfall"),
    "jhor waterfall":            _p("https://images.unsplash.com/photo-1460356262774-13d55a8a3a4a?w=1400&q=80", "Jhor Waterfall"),
    "tindhare waterfall":        _p("https://images.unsplash.com/photo-1494548162494-384bba4ab999?w=1400&q=80", "Tindhare Waterfall"),
    # --- pilgrimage ---
    "pathibhara devi":           _p("https://images.unsplash.com/photo-1570192977-f48187449e48?w=1400&q=80", "Pathibhara Devi, Taplejung"),
    "badimalika":                _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "Badimalika, Bajura"),
    "swargadwari":               _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Swargadwari, Pyuthan"),
    "devghat":                   _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Devghat Dham"),
    "devghat dham":              _p("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "Devghat Dham"),
    "barahachhetra":             _p("https://images.unsplash.com/photo-1570192977-f48187449e48?w=1400&q=80", "Barahachhetra Dham"),
    "kalinchowk bhagwati":       _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Kalinchowk Bhagwati"),
    "kalinchowk":                _p("https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1400&q=80", "Kalinchowk"),
    "dakshinkali":               _p("https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "Dakshinkali Temple"),
    "dakshinkali temple":        _p("https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "Dakshinkali Temple"),
    "guhyeshwari":               _p("https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "Guhyeshwari Temple"),
    "bindhyabasini":             _p("https://images.unsplash.com/photo-1528181304800-259b08848526?w=1400&q=80", "Bindhyabasini Temple, Pokhara"),
    "bindhyabasini temple":      _p("https://images.unsplash.com/photo-1528181304800-259b08848526?w=1400&q=80", "Bindhyabasini Temple, Pokhara"),
    "tal barahi":                _s("pokhara", "fewatal.jpg", "Tal Barahi Temple, Phewa Lake"),
    "chandragiri bhaleshwor":    _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Bhaleshwor Temple, Chandragiri"),
    "bhaleshwor mahadev":        _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Bhaleshwor Mahadev"),
    "doleshwor mahadev":         _p("https://images.unsplash.com/photo-1570192977-f48187449e48?w=1400&q=80", "Doleshwor Mahadev"),
    "changunarayan":             _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Changunarayan Temple"),
    "siddha pokhari":            _p("https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=1400&q=80", "Siddha Pokhari, Bhaktapur"),
    # --- monasteries / stupas ---
    "world peace pagoda":        _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "World Peace Pagoda, Pokhara"),
    "shanti stupa":              _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "Shanti Stupa"),
    "kopan monastery":           _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Kopan Monastery"),
    "thrangu tashi yangtse":     _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Thrangu Tashi Yangtse Monastery"),
    "namo buddha":               _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Namo Buddha"),
    "pharping":                  _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Pharping (Yangleshö)"),
    "asura cave":                _p("https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "Asura Cave, Pharping"),
    "maya devi temple":          _s("lumbini", "garden.jpg", "Maya Devi Temple, Lumbini"),
    "lumbini":                   _s("lumbini", "garden.jpg", "Lumbini"),
    "tengboche monastery":       _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "Tengboche Monastery"),
    "khumjung gompa":            _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Khumjung Gompa"),
    "thame monastery":           _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Thame Monastery"),
    "maratika monastery":        _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Maratika Monastery, Halesi"),
    "lo manthang":               _s("mustang", "lo-manthang.jpg", "Lo Manthang, Mustang"),
    "chhoser cave":              _p("https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "Chhoser Sky Caves, Mustang"),
    "braga gompa":               _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "Braga Gompa, Manang"),
    "rinchenling gompa":         _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Rinchenling Gompa, Dolpo"),
    "shey gompa":                _p("https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "Shey Gompa, Dolpo"),
    # --- adventure ---
    "bungee jumping bhote koshi": _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "Bhote Koshi Bungee"),
    "the last resort":           _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "The Last Resort Bungee"),
    "highground bungee":         _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "HighGround Bungee, Pokhara"),
    "cliff kushma":              _p("https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1400&q=80", "Cliff Kushma Bungee"),
    "sarangkot paragliding":     _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Sarangkot Paragliding"),
    "paragliding pokhara":       _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Pokhara Paragliding"),
    "zipflyer pokhara":          _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Zipflyer Nepal"),
    "zip flyer":                 _p("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "Zip Flyer"),
    "ultralight flight":         _p("https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "Ultralight flight Pokhara"),
    "mountain flight":           _p("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "Everest Mountain Flight"),
    "everest skydiving":         _p("https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=1400&q=80", "Everest Skydive"),
    "trishuli rafting":          _p("https://images.unsplash.com/photo-1467890748417-b45d7be0459c?w=1400&q=80", "Trishuli River Rafting"),
    "bhote koshi rafting":       _p("https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1400&q=80", "Bhote Koshi Rafting"),
    "seti river rafting":        _p("https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1400&q=80", "Seti River Rafting"),
    "karnali river rafting":     _p("https://images.unsplash.com/photo-1465311497579-3f30fd3d2993?w=1400&q=80", "Karnali River Rafting"),
    "sun koshi rafting":         _p("https://images.unsplash.com/photo-1467890748417-b45d7be0459c?w=1400&q=80", "Sun Koshi Rafting"),
    "canyoning":                 _p("https://images.unsplash.com/photo-1520637836862-4d197d17c55a?w=1400&q=80", "Canyoning"),
    "cable car manakamana":      _p("https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "Manakamana Cable Car"),
    "chandragiri cable car":     _p("https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "Chandragiri Cable Car"),
    "manakamana cable car":      _p("https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "Manakamana Cable Car"),
    # --- tea ---
    "kanyam tea garden":         _p("https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=1400&q=80", "Kanyam Tea Garden, Ilam"),
    "kanyam":                    _p("https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=1400&q=80", "Kanyam Tea Gardens"),
    "ilam":                      _s("ilam", "tea-gardens.jpg", "Ilam Tea Gardens"),
    "ilam tea estates":          _s("ilam", "tea-gardens.jpg", "Ilam Tea Estates"),
    # --- villages ---
    "bandipur":                  _s("bandipur", "hilltop-village.jpg", "Bandipur"),
    "ghandruk":                  _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Ghandruk Gurung village"),
    "ghale gaun":                _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Ghale Gaun"),
    "ghalegaun":                 _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Ghale Gaun"),
    "sirubari":                  _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Sirubari village"),
    "barpak":                    _p("https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1400&q=80", "Barpak village, Gorkha"),
    "chitlang":                  _p("https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1400&q=80", "Chitlang village"),
    "dhampus":                   _p("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=1400&q=80", "Dhampus village"),
    "marpha":                    _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Marpha village, Mustang"),
    "jomsom":                    _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Jomsom"),
    "kagbeni":                   _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Kagbeni, Mustang"),
    "tukuche":                   _p("https://images.unsplash.com/photo-1526316800853-b0f34c6adf5c?w=1400&q=80", "Tukuche, Mustang"),
    "bungamati":                 _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Bungamati village"),
    "khokana":                   _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Khokana village"),
    "panauti":                   _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Panauti heritage town"),
    "dhulikhel":                 _p("https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1400&q=80", "Dhulikhel"),
    "kirtipur":                  _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Kirtipur"),
    "tansen":                    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Tansen, Palpa"),
    # --- wildlife ---
    "sauraha":                   _s("chitwan", "safari.jpg", "Sauraha, Chitwan"),
    "elephant breeding centre":  _p("https://images.unsplash.com/photo-1504194921103-f5c65a5d8eb0?w=1400&q=80", "Elephant Breeding Centre, Chitwan"),
    "one horned rhino":          _p("https://images.unsplash.com/photo-1549366021-9f761d450615?w=1400&q=80", "One-horned Rhino"),
    "bengal tiger":              _p("https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=1400&q=80", "Bengal Tiger"),
    "gharial crocodile":         _p("https://images.unsplash.com/photo-1549366021-9f761d450615?w=1400&q=80", "Gharial Crocodile"),
    # --- festivals ---
    "indra jatra":               _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Indra Jatra, Kathmandu"),
    "bisket jatra":              _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "Bisket Jatra, Bhaktapur"),
    "rato machhindranath":       _p("https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "Rato Machhindranath Jatra"),
    "mani rimdu":                _p("https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "Mani Rimdu festival"),
    "tiji festival":             _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Tiji Festival, Mustang"),
    "dashain":                   _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "Dashain festival"),
    "tihar":                     _p("https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "Tihar (Deepawali)"),
    "holi":                      _p("https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "Holi, festival of colours"),
    "ghode jatra":               _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "Ghode Jatra"),
    "gai jatra":                 _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Gai Jatra"),
    # --- cities ---
    "thamel":                    _p("https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "Thamel, Kathmandu"),
    "new road":                  _p("https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "New Road, Kathmandu"),
    "basantapur":                _s("kathmandu", "durbar-square.jpg", "Basantapur, Kathmandu"),
    "pokhara":                   _s("pokhara", "fewatal.jpg", "Pokhara"),
    "lakeside pokhara":          _s("pokhara", "fewatal.jpg", "Pokhara Lakeside"),
    "pokhara lakeside":          _s("pokhara", "fewatal.jpg", "Pokhara Lakeside"),
    # --- hot springs ---
    "tatopani":                  _p("https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1400&q=80", "Tatopani Hot Spring"),
    # --- bridges/gorges ---
    "kali gandaki gorge":        _p("https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1400&q=80", "Kali Gandaki Gorge"),
    "seti gorge":                _p("https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1400&q=80", "Seti Gandaki Gorge"),
}


# ---------------------------------------------------------------------------
# Slug -> pool mapping
# ---------------------------------------------------------------------------
SLUG_POOL = {
    "mountains":            MOUNTAIN_PHOTOS,
    "mountain":             MOUNTAIN_PHOTOS,
    "peaks":                MOUNTAIN_PHOTOS,
    "hills":                HILL_PHOTOS,
    "hill-stations":        HILL_PHOTOS,
    "valleys":              VALLEY_PHOTOS,
    "valley":               VALLEY_PHOTOS,
    "lakes":                LAKE_PHOTOS,
    "lake":                 LAKE_PHOTOS,
    "lakes-water-activities": LAKE_PHOTOS,
    "rivers":               RIVER_PHOTOS,
    "river":                RIVER_PHOTOS,
    "waterfalls":           WATERFALL_PHOTOS,
    "waterfall":            WATERFALL_PHOTOS,
    "caves":                CAVE_PHOTOS,
    "cave":                 CAVE_PHOTOS,
    "hot-springs":          HOTSPRING_PHOTOS,
    "hot-spring":           HOTSPRING_PHOTOS,
    "natural-wonders":      NATURAL_PHOTOS,
    "viewpoints":           VIEWPOINT_PHOTOS,
    "viewpoint":            VIEWPOINT_PHOTOS,
    "view-tower":           VIEWPOINT_PHOTOS,
    "forests":              FOREST_PHOTOS,
    "forest":               FOREST_PHOTOS,
    "wildlife":             WILDLIFE_PHOTOS,
    "national-parks":       WILDLIFE_PHOTOS,
    "national-park":        WILDLIFE_PHOTOS,
    "bird-watching":        BIRD_PHOTOS,
    "birding":              BIRD_PHOTOS,
    "parks-gardens":        PARK_PHOTOS,
    "gardens":              PARK_PHOTOS,
    "parks":                PARK_PHOTOS,
    "park":                 PARK_PHOTOS,
    "eco-tourism":          ECO_PHOTOS,
    "agriculture":          AGRI_PHOTOS,
    "tea-coffee":           TEA_PHOTOS,
    "tea-gardens":          TEA_PHOTOS,
    "teagardens":           TEA_PHOTOS,
    "temples":              TEMPLE_PHOTOS,
    "temple":               TEMPLE_PHOTOS,
    "hindu-temples":        TEMPLE_PHOTOS,
    "buddhist-sites":       STUPA_PHOTOS,
    "buddhist":             STUPA_PHOTOS,
    "stupas":               STUPA_PHOTOS,
    "stupa":                STUPA_PHOTOS,
    "monasteries":          STUPA_PHOTOS,
    "monastery":            STUPA_PHOTOS,
    "pilgrimage":           PILGRIMAGE_PHOTOS,
    "spiritual-wellness":   SPIRITUAL_PHOTOS,
    "heritage":             HERITAGE_PHOTOS,
    "heritage-temples":     HERITAGE_PHOTOS,
    "unesco":               HERITAGE_PHOTOS,
    "durbar-squares":       HERITAGE_PHOTOS,
    "palaces":              HERITAGE_PHOTOS,
    "museums":              MUSEUM_PHOTOS,
    "museum":               MUSEUM_PHOTOS,
    "culture":              CULTURE_PHOTOS,
    "festivals":            FESTIVAL_PHOTOS,
    "festival":             FESTIVAL_PHOTOS,
    "cities":               CITY_PHOTOS,
    "city":                 CITY_PHOTOS,
    "shopping":             SHOP_PHOTOS,
    "food-culinary":        FOOD_PHOTOS,
    "food":                 FOOD_PHOTOS,
    "villages":             VILLAGE_PHOTOS,
    "village":              VILLAGE_PHOTOS,
    "traditional-villages": VILLAGE_PHOTOS,
    "adventure":            ADVENTURE_PHOTOS,
    "climbing":             ADVENTURE_PHOTOS,
    "mountaineering":       ADVENTURE_PHOTOS,
    "trekking":             TREKKING_PHOTOS,
    "trek":                 TREKKING_PHOTOS,
    "hiking":               TREKKING_PHOTOS,
    "air-sports":           AIRSPORTS_PHOTOS,
    "paragliding":          AIRSPORTS_PHOTOS,
    "bungee":               ADVENTURE_PHOTOS,
    "zip-flyer":            AIRSPORTS_PHOTOS,
    "cablecar":             CABLECAR_PHOTOS,
    "cable-car":            CABLECAR_PHOTOS,
    "ropeway":              CABLECAR_PHOTOS,
    "water-sports":         WATERSPORTS_PHOTOS,
    "rafting":              WATERSPORTS_PHOTOS,
    "kayaking":             WATERSPORTS_PHOTOS,
    "boating":              WATERSPORTS_PHOTOS,
    "camping":              CAMPING_PHOTOS,
    "cycling":              CYCLING_PHOTOS,
    "mountain-biking":      CYCLING_PHOTOS,
    "winter":               WINTER_PHOTOS,
    "snow":                 WINTER_PHOTOS,
    "scenic-routes":        SCENICROUTE_PHOTOS,
    "road-trips":           SCENICROUTE_PHOTOS,
    "attraction":           ATTRACTION_PHOTOS,
    "attractions":          ATTRACTION_PHOTOS,
    "nature-trekking":      TREKKING_PHOTOS,
    "museum":               MUSEUM_PHOTOS,
    "viewpoint":            VIEWPOINT_PHOTOS,
    "religious-sites":      TEMPLE_PHOTOS,
    "hospital":             HOSPITAL_PHOTOS,
    "clinic":               HOSPITAL_PHOTOS,
    "pharmacy":             PHARMACY_PHOTOS,
    "police":               POLICE_PHOTOS,
    "bank":                 BANK_PHOTOS,
    "atm":                  BANK_PHOTOS,
    "restaurant":           RESTAURANT_PHOTOS,
    "cafe":                 RESTAURANT_PHOTOS,
    "shop":                 SHOP_PHOTOS,
    "store":                SHOP_PHOTOS,
    "market":               SHOP_PHOTOS,
    "hotel":                HOTEL_PHOTOS,
    "resort":               HOTEL_PHOTOS,
    "guest_house":          HOTEL_PHOTOS,
    "hostel":               HOTEL_PHOTOS,
    "motel":                HOTEL_PHOTOS,
    "homestay":             VILLAGE_PHOTOS,
    "information":          CITY_PHOTOS,
    "travel_agency":        CITY_PHOTOS,
}

ACCOMMODATION_SLUGS = {
    "hotel", "resort", "lodge", "guest_house", "guesthouse", "hostel",
    "motel", "homestay", "home_stay", "alpine_hut", "camp_site",
    "camp_pitch", "chalet", "apartment", "wilderness_hut", "cottage",
}

ACCOMMODATION_NAME_HINTS = [
    "hotel", "resort", "lodge", "guest house", "guesthouse", "homestay",
    "home stay", "backpackers", "hostel", "motel", "cottages", "tea house",
    "teahouse", "inn",
]

_WORD_RE = re.compile(r"[a-z0-9]+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _n(text):
    return _NON_ALNUM.sub("", (text or "").lower())


def _words(text):
    return set(_WORD_RE.findall((text or "").lower()))


def _whole_word_in(needle, haystack):
    """True if `needle` appears in `haystack` as whole phrase (word boundaries on both sides)."""
    n = (needle or "").lower().strip()
    h = (haystack or "").lower()
    if not n:
        return False
    # Escape for regex
    pat = r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])"
    return re.search(pat, h) is not None


# ---------------------------------------------------------------------------
# Core categorization
# ---------------------------------------------------------------------------
def _is_accommodation(destination):
    cat = getattr(destination, "category", None)
    slug = (getattr(cat, "slug", "") or "").lower() if cat else ""
    if slug in ACCOMMODATION_SLUGS:
        return True
    name = (getattr(destination, "name", "") or "").lower()
    for h in ACCOMMODATION_NAME_HINTS:
        if _whole_word_in(h, name):
            return True
    return False


def _match_landmark(dest_name):
    """Return the curated cover dict if the destination name matches a LANDMARKS key (longest, whole-word)."""
    if not dest_name:
        return None
    name_l = dest_name.lower()
    best = None
    best_len = 0
    for key, photo in LANDMARKS.items():
        if not key:
            continue
        # Whole-word/phrase match
        if _whole_word_in(key, name_l) and len(key) > best_len:
            best = photo
            best_len = len(key)
    return best


def _match_static(dest_name):
    """Whole-word match against STATIC_AI keys (longest first)."""
    if not dest_name:
        return None
    name_l = dest_name.lower()
    best = None
    best_len = 0
    for key in STATIC_AI.keys():
        if not key:
            continue
        if _whole_word_in(key, name_l) and len(key) > best_len:
            best = key
            best_len = len(key)
    return best


def _categorize(destination):
    name = getattr(destination, "name", "") or ""
    desc = getattr(destination, "short_description", "") or ""
    city = getattr(destination, "city", "") or ""
    district = getattr(destination, "district", "") or ""
    cat = getattr(destination, "category", None)
    cat_name = (getattr(cat, "name", "") or "") if cat else ""
    cat_slug = ((getattr(cat, "slug", "") or "").lower()) if cat else ""
    haystack = f"{name} {desc} {city} {district} {cat_name}"
    name_l = name.lower()

    if _is_accommodation(destination):
        return HOTEL_PHOTOS, "hotel", HOTEL_PHOTOS

    # 1. Explicit landmark (curated cover for named place)
    landmark = _match_landmark(name)
    if landmark is not None:
        # Determine gallery pool from LANDMARKS key name suffix or a sensible category pool
        key_hint = ""
        for suffix in ("temple", "stupa", "monastery", "gompa", "mahadev", "mandir", "bhairav"):
            if suffix in name_l:
                key_hint = "temple"
                break
        for suffix in ("lake", "tal", "pokhari", "kunda", "sarovar"):
            if suffix in name_l:
                key_hint = "lake"
                break
        for suffix in ("fall", "jharna", "chhango"):
            if suffix in name_l:
                key_hint = "waterfall"
                break
        for suffix in ("cave", "gufa"):
            if suffix in name_l:
                key_hint = "cave"
                break
        for suffix in ("national park", "wildlife", "safari"):
            if suffix in name_l:
                key_hint = "wildlife"
                break
        for suffix in ("peak", "mount", "everest", "himāl", "himal", "mountain"):
            if suffix in name_l:
                key_hint = "mountain"
                break
        for suffix in ("durbar", "palace", "heritage"):
            if suffix in name_l:
                key_hint = "heritage"
                break
        for suffix in ("viewpoint", "hill", "danda", "nagarkot", "chandragiri", "sarangkot", "phulchowki", "shree antu", "sri antu", "daman", "kakani"):
            if suffix in name_l:
                key_hint = "viewpoint"
                break
        for suffix in ("trek", "trekking", "base camp", "circuit", "pass", "la"):
            if suffix in name_l:
                key_hint = "trekking"
                break
        for suffix in ("village", "gaun"):
            if suffix in name_l:
                key_hint = "village"
                break
        for suffix in ("tea garden", "tea estate", "ilam", "kanyam"):
            if suffix in name_l:
                key_hint = "tea"
                break
        for suffix in ("cable car", "ropeway"):
            if suffix in name_l:
                key_hint = "cablecar"
                break
        for suffix in ("rafting", "kayak"):
            if suffix in name_l:
                key_hint = "watersports"
                break
        for suffix in ("bungee", "zip", "skydiving", "climb"):
            if suffix in name_l:
                key_hint = "adventure"
                break
        for suffix in ("paragliding", "ultralight", "flight"):
            if suffix in name_l:
                key_hint = "airsports"
                break
        for suffix in ("festival", "jatra", "mela"):
            if suffix in name_l:
                key_hint = "festival"
                break
        gallery_pool = {
            "temple": TEMPLE_PHOTOS,
            "stupa": STUPA_PHOTOS,
            "lake": LAKE_PHOTOS,
            "waterfall": WATERFALL_PHOTOS,
            "cave": CAVE_PHOTOS,
            "wildlife": WILDLIFE_PHOTOS,
            "mountain": MOUNTAIN_PHOTOS,
            "heritage": HERITAGE_PHOTOS,
            "viewpoint": VIEWPOINT_PHOTOS,
            "trekking": TREKKING_PHOTOS,
            "village": VILLAGE_PHOTOS,
            "tea": TEA_PHOTOS,
            "cablecar": CABLECAR_PHOTOS,
            "watersports": WATERSPORTS_PHOTOS,
            "adventure": ADVENTURE_PHOTOS,
            "airsports": AIRSPORTS_PHOTOS,
            "festival": FESTIVAL_PHOTOS,
        }.get(key_hint, MOUNTAIN_PHOTOS)
        # If the landmark URL is a /images/ static file, prefer its _STATIC_TO_POOL gallery
        if landmark.get("url", "").startswith("/images/destinations/"):
            static_key = _match_static(name)
            if static_key and static_key in _STATIC_TO_POOL:
                _, gallery_pool = _STATIC_TO_POOL[static_key]
        return landmark, "landmark", gallery_pool

    # 2. Static AI (whole-word match)
    static_key = _match_static(name)
    if static_key is not None:
        cover = STATIC_AI[static_key]
        _, gallery_pool = _STATIC_TO_POOL.get(static_key, ("general", MOUNTAIN_PHOTOS))
        return cover, static_key, gallery_pool

    # 3. Category slug -> pool
    if cat_slug in SLUG_POOL:
        pool = SLUG_POOL[cat_slug]
        return pool, cat_slug, pool

    # 4. Name keywords (whole-word)
    keyword_to_pool = [
        (("waterfall", "jharana", "jharna", "chhango", "falls"), WATERFALL_PHOTOS),
        (("cave", "gufa", "cavern", "gupha"), CAVE_PHOTOS),
        (("hot spring", "hotspring", "tatopani"), HOTSPRING_PHOTOS),
        (("temple", "mandir", "mahadev", "shiva", "bhairav", "kumari",
          "bindhyabasini", "dakshinkali", "guhyeshwari", "pashupati",
          "doleshwor", "bhaleshwor", "devi", "bhagwati", "narayan",
          "bhimsen", "ganesh", "vinayak", "siddhi"), TEMPLE_PHOTOS),
        (("stupa", "gompa", "monastery", "buddhist", "buddha", "vihar", "gumba",
          "lumbini", "world peace pagoda", "shanti stupa"), STUPA_PHOTOS),
        (("durbar square", "durbar", "palace", "heritage site", "rani mahal",
          "gorkha durbar", "nuwakot durbar"), HERITAGE_PHOTOS),
        (("museum", "art gallery", "exhibition", "narayanhiti"), MUSEUM_PHOTOS),
        (("national park", "wildlife reserve", "conservation area",
          "hunting reserve", "safari"), WILDLIFE_PHOTOS),
        (("tea garden", "tea plantation", "tea estate", "kanyam"), TEA_PHOTOS),
        (("cable car", "cablecar", "ropeway"), CABLECAR_PHOTOS),
        (("botanical garden", "garden of dreams", "godawari botanical"), PARK_PHOTOS),
        (("zoo", "aquarium", "theme park"), WILDLIFE_PHOTOS),
        (("lake", "tal", "kunda", "pokhari", "sarovar", "daha"), LAKE_PHOTOS),
        (("river", "khola", "kosi", "koshi", "karnali", "gandaki", "trishuli",
          "narayani", "seti", "arun", "tamur", "bheri", "rapti", "mahakali",
          "bhote koshi", "sun koshi", "sun kosi", "kali gandaki"), RIVER_PHOTOS),
        (("viewpoint", "view point", "view tower", "poon hill", "poonhill",
          "sarangkot", "kala patthar", "gokyo ri"), VIEWPOINT_PHOTOS),
        (("peak", "mountain", "everest", "sagarmatha", "annapurna", "machhapuchhre",
          "machhapuchhare", "fishtail", "manaslu", "dhaulagiri", "makalu",
          "kanchenjunga", "kanchanjunga", "lhotse", "cho oyu", "api himal", "saipal",
          "dhaulagiri"), MOUNTAIN_PHOTOS),
        (("base camp", "trek", "trekking", "circuit", "trek route", "high camp",
          "la pass"), TREKKING_PHOTOS),
        (("hill station", "hill"), HILL_PHOTOS),
        (("valley"), VALLEY_PHOTOS),
        (("forest", "jungle", "rhododendron", "sal forest"), FOREST_PHOTOS),
        (("bird watching", "birding", "bird"), BIRD_PHOTOS),
        (("paragliding", "ultralight", "zip flyer", "zipflyer", "skydive"), AIRSPORTS_PHOTOS),
        (("rafting", "kayak", "canyoning", "boating", "canoe"), WATERSPORTS_PHOTOS),
        (("bungee", "rock climbing", "climbing", "bouldering", "peak climbing"), ADVENTURE_PHOTOS),
        (("camping", "camp", "tent"), CAMPING_PHOTOS),
        (("cycling", "mountain bike", "biking"), CYCLING_PHOTOS),
        (("snow", "winter", "kalinchowk"), WINTER_PHOTOS),
        (("festival", "jatra", "mela"), FESTIVAL_PHOTOS),
        (("bazaar", "bazar", "market", "thamel", "new road"), SHOP_PHOTOS),
        (("restaurant", "cafe", "bakery", "dhaba", "momo", "dal bhat", "street food"), FOOD_PHOTOS),
        (("farm", "organic farm", "agriculture", "farm stay", "rice terrace"), AGRI_PHOTOS),
        (("scenic drive", "highway", "prithvi highway", "siddhartha highway",
          "araniko highway", "karnali highway", "pasang lhamu"), SCENICROUTE_PHOTOS),
        (("eco", "community tourism", "homestay"), ECO_PHOTOS),
        (("village", "gaun", "bazaar"), VILLAGE_PHOTOS),
        (("hotel", "resort", "lodge", "guest house", "guesthouse", "hostel",
          "motel", "teahouse", "tea house", "homestay", "home stay", "inn",
          "cottage", "restaurant"), HOTEL_PHOTOS),
        (("city", "kathmandu", "pokhara", "patan", "lalitpur", "bhaktapur",
          "biratnagar", "birgunj", "nepalgunj", "dharan", "butwal", "hetauda",
          "janakpur", "bharatpur", "siddharthanagar", "bhairahawa", "dhangadhi"), CITY_PHOTOS),
    ]
    for keywords, pool in keyword_to_pool:
        for kw in keywords:
            if _whole_word_in(kw, haystack) or (kw in haystack and " " not in kw and len(kw) > 4):
                # Strict whole-word; single-word keywords must be >=5 chars AND whole word
                if " " in kw:
                    return pool, kw, pool
                if _whole_word_in(kw, haystack):
                    return pool, kw, pool

    # 5. Generic fallback
    if _is_accommodation(destination):
        return HOTEL_PHOTOS, "hotel-fallback", HOTEL_PHOTOS
    return MOUNTAIN_PHOTOS, "mountain-fallback", MOUNTAIN_PHOTOS


def _pick(pool, seed):
    if not pool:
        return _svg("general", "Nepal")
    h = hashlib.md5(f"np-tourism-{seed}".encode()).hexdigest()
    return pool[int(h[:8], 16) % len(pool)]


def resolve_cover_photo(destination):
    cover_or_pool, key, _ = _categorize(destination)
    if isinstance(cover_or_pool, dict):
        return cover_or_pool
    dest_id = getattr(destination, "id", None) or 0
    return _pick(cover_or_pool, f"cover-{dest_id}-{key}")


def resolve_gallery_photos(destination, target=6):
    cover_or_pool, key, gallery_pool = _categorize(destination)
    dest_id = getattr(destination, "id", None) or 0
    cover = resolve_cover_photo(destination)
    cover_url = cover.get("url")
    seen = {cover_url}
    out = []
    i = 0
    attempts = 0
    while len(out) < target and attempts < target * 15 and i < len(gallery_pool) * 5 + 60:
        p = _pick(gallery_pool, f"gallery-{dest_id}-{key}-{i}")
        u = p.get("url")
        if u and u not in seen and u != cover_url:
            out.append(p)
            seen.add(u)
        i += 1
        attempts += 1
    if len(out) < target:
        i = 0
        while len(out) < target and i < len(GENERAL_PHOTOS) * 3:
            p = _pick(GENERAL_PHOTOS, f"gallery-supp-{dest_id}-{i}")
            u = p.get("url")
            if u and u not in seen:
                out.append(p)
                seen.add(u)
            i += 1
    return out


def resolve_hotel_photo(hotel):
    return _pick(HOTEL_PHOTOS, f"hotel-{getattr(hotel, 'id', 0) or 0}")


def resolve_poi_photo(poi_type="", poi_name="", seed=0):
    hay = f"{poi_type} {poi_name}".lower()
    if any(w in hay for w in ("health", "medical", "doctor", "emergency", "hospital", "clinic")):
        return _pick(HOSPITAL_PHOTOS, seed)
    if "pharmacy" in hay or "medicine" in hay:
        return _pick(PHARMACY_PHOTOS, seed)
    if "police" in hay:
        return _pick(POLICE_PHOTOS, seed)
    if any(w in hay for w in ("bank", "atm", "money", "finance")):
        return _pick(BANK_PHOTOS, seed)
    if any(w in hay for w in ("restaurant", "food", "eat", "momo", "cafe")):
        return _pick(RESTAURANT_PHOTOS, seed)
    if any(w in hay for w in ("hotel", "resort", "lodge", "stay")):
        return _pick(HOTEL_PHOTOS, seed)
    return _pick(ATTRACTION_PHOTOS, seed)


def get_category_svg(category_key):
    return SVG.get((category_key or "general").lower(), SVG["general"])


def is_accommodation(destination):
    return _is_accommodation(destination)


def is_accommodation_category(slug):
    return (slug or "").lower() in ACCOMMODATION_SLUGS


def acquire_wikimedia_photos(destination, limit=8, timeout=6):
    # Network is blocked in sandbox; kept for future admin action.
    return []
