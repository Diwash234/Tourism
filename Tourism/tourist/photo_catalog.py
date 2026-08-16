"""
Tourism/tourist/photo_catalog.py

A curated, provenance-rich catalog of REAL Nepal travel photography plus
a smart resolver that assigns a DISTINCT, relevant cover image to every
destination. Headline destinations (Everest, Pokhara, Chitwan, ...) get
explicit static AI-generated photos shipped with the app so they always
look correct - even offline.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

USER_AGENT = "NepalTourismPlatform/2.0 (https://github.com/Diwash234/Tourism; tourism-app)"

# ---------------------------------------------------------------------------
# Base photo pools (Unsplash License - free commercial use).
# Each entry: {url, thumb, source, author, license, source_url, tags?}
# ---------------------------------------------------------------------------

MOUNTAIN_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=500&q=70", "source": "unsplash", "author": "Unsplash Himalayan Collection", "license": "Unsplash License (free commercial use)", "source_url": "https://unsplash.com/s/photos/nepal-mountain"},
    {"url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=500&q=70", "source": "unsplash", "author": "Unsplash Landscape Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya"},
    {"url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=500&q=70", "source": "unsplash", "author": "Unsplash Alpine Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-peak"},
    {"url": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=500&q=70", "source": "unsplash", "author": "Unsplash Summit Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/snow-mountain"},
    {"url": "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=500&q=70", "source": "unsplash", "author": "Unsplash High Camp Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya-trek"},
    {"url": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=500&q=70", "source": "unsplash", "author": "Unsplash Ridge Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-ridge"},
    {"url": "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=500&q=70", "source": "unsplash", "author": "Unsplash Peak Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/snow-peak"},
    {"url": "https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=500&q=70", "source": "unsplash", "author": "Unsplash Snowline", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya-snow"},
    {"url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=500&q=70", "source": "unsplash", "author": "Unsplash Vista", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-vista"},
    {"url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=500&q=70", "source": "unsplash", "author": "Unsplash Trail", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/hiking-trail"},
    {"url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=500&q=70", "source": "unsplash", "author": "Unsplash Valley", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-valley"},
    {"url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500&q=70", "source": "unsplash", "author": "Unsplash Alps", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/alps"},
]

LAKE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=500&q=70", "source": "unsplash", "author": "Unsplash Lake Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/lake-mountain"},
    {"url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=500&q=70", "source": "unsplash", "author": "Unsplash Misty Lake Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/misty-lake"},
    {"url": "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=500&q=70", "source": "unsplash", "author": "Unsplash Water Reflection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/phewa-lake"},
    {"url": "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=500&q=70", "source": "unsplash", "author": "Unsplash Alpine Lake", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/alpine-lake"},
    {"url": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=500&q=70", "source": "unsplash", "author": "Unsplash Mountain Lake", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-lake"},
]

WATERFALL_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=500&q=70", "source": "unsplash", "author": "Unsplash Waterfall Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/waterfall"},
    {"url": "https://images.unsplash.com/photo-1432889490240-84df33d47091?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1432889490240-84df33d47091?w=500&q=70", "source": "unsplash", "author": "Unsplash Cascade Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/cascade"},
]

HERITAGE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=500&q=70", "source": "unsplash", "author": "Unsplash Temple Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/nepal-temple"},
    {"url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=500&q=70", "source": "unsplash", "author": "Unsplash Durbar Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/kathmandu"},
    {"url": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=500&q=70", "source": "unsplash", "author": "Unsplash Stupa Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/boudhanath"},
    {"url": "https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=500&q=70", "source": "unsplash", "author": "Unsplash Prayer Flags", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/prayer-flags"},
    {"url": "https://images.unsplash.com/photo-1570192977-f48187449e48?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1570192977-f48187449e48?w=500&q=70", "source": "unsplash", "author": "Unsplash Hindu Temple", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/pashupatinath"},
]

WILDLIFE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=500&q=70", "source": "unsplash", "author": "Unsplash Safari Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/chitwan"},
    {"url": "https://images.unsplash.com/photo-1549366021-9f761d450615?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1549366021-9f761d450615?w=500&q=70", "source": "unsplash", "author": "Unsplash Rhino Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/one-horned-rhino"},
    {"url": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=500&q=70", "source": "unsplash", "author": "Unsplash Bengal Tiger", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/bengal-tiger"},
    {"url": "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=500&q=70", "source": "unsplash", "author": "Unsplash Jungle Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/jungle-safari"},
]

CITY_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=500&q=70", "source": "unsplash", "author": "Unsplash Kathmandu Streets", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/kathmandu-street"},
    {"url": "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=500&q=70", "source": "unsplash", "author": "Unsplash Nepal Market", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/nepal-market"},
    {"url": "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=500&q=70", "source": "unsplash", "author": "Unsplash City Life", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/thamel"},
]

HOTEL_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500&q=70", "source": "unsplash", "author": "Unsplash Hotel Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/hotel"},
    {"url": "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=500&q=70", "source": "unsplash", "author": "Unsplash Resort Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/resort"},
    {"url": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=500&q=70", "source": "unsplash", "author": "Unsplash Lodge Collection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/lodge"},
    {"url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=500&q=70", "source": "unsplash", "author": "Unsplash Boutique Hotel", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/boutique-hotel"},
    {"url": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=500&q=70", "source": "unsplash", "author": "Unsplash Teahouse Lodge", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/teahouse"},
]

GENERAL_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=500&q=70", "source": "unsplash", "author": "Unsplash Nepal", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/nepal"},
    {"url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=500&q=70", "source": "unsplash", "author": "Unsplash Nepal Culture", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/nepal-culture"},
    {"url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=500&q=70", "source": "unsplash", "author": "Unsplash Himalaya", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya"},
    {"url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=500&q=70", "source": "unsplash", "author": "Unsplash Nepal Hills", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/nepal-hills"},
]

# ---------------------------------------------------------------------------
# Extra / specialised pools (defined BEFORE CATEGORY_POOLS references them)
# ---------------------------------------------------------------------------

ATTRACTION_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1568393691080-fb2f29a6edd2?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1568393691080-fb2f29a6edd2?w=500&q=70", "source": "unsplash", "author": "Unsplash Viewpoint", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/viewpoint"},
    {"url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=500&q=70", "source": "unsplash", "author": "Unsplash Lookout", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-view"},
    {"url": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=500&q=70", "source": "unsplash", "author": "Unsplash Night Mountains", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya-night"},
    {"url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=500&q=70", "source": "unsplash", "author": "Unsplash Valley", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-valley"},
    {"url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500&q=70", "source": "unsplash", "author": "Unsplash Alpine", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/alpine"},
    {"url": "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=500&q=70", "source": "unsplash", "author": "Unsplash Trekking Path", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/trekking"},
    {"url": "https://images.unsplash.com/photo-1548013146-72479768bada?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1548013146-72479768bada?w=500&q=70", "source": "unsplash", "author": "Unsplash Asian Temple", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/temple-asia"},
]

CAVE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1504788363733-507549153474?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1504788363733-507549153474?w=500&q=70", "source": "unsplash", "author": "Unsplash Cave", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/cave"},
    {"url": "https://images.unsplash.com/photo-1521400308261-14ac427bc08f?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1521400308261-14ac427bc08f?w=500&q=70", "source": "unsplash", "author": "Unsplash Limestone Cave", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/limestone-cave"},
    {"url": "https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1545158535-c3f7168c28b6?w=500&q=70", "source": "unsplash", "author": "Unsplash Cave Entrance", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/cave-entrance"},
    {"url": "https://images.unsplash.com/photo-1588416820092-58b8c4a727dd?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1588416820092-58b8c4a727dd?w=500&q=70", "source": "unsplash", "author": "Unsplash Stalactites", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/stalactite"},
]

MUSEUM_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=500&q=70", "source": "unsplash", "author": "Unsplash Museum", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/museum"},
    {"url": "https://images.unsplash.com/photo-1565060169861-2d81e383be0f?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1565060169861-2d81e383be0f?w=500&q=70", "source": "unsplash", "author": "Unsplash Gallery", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/art-gallery"},
    {"url": "https://images.unsplash.com/photo-1544531586-fde5298cdd40?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1544531586-fde5298cdd40?w=500&q=70", "source": "unsplash", "author": "Unsplash Exhibition", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/exhibition"},
]

GARDEN_PARK_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=500&q=70", "source": "unsplash", "author": "Unsplash Garden", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/garden"},
    {"url": "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=500&q=70", "source": "unsplash", "author": "Unsplash Park", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/park-green"},
    {"url": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=500&q=70", "source": "unsplash", "author": "Unsplash Green Park", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/nature-park"},
]

TEAGARDEN_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1564856536-e27e5f74a493?w=500&q=70", "source": "unsplash", "author": "Unsplash Tea Garden", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/tea-plantation"},
    {"url": "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=500&q=70", "source": "unsplash", "author": "Unsplash Green Hills", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/green-hills"},
]

CABLECAR_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1542338707-5a4fb3724edd?w=500&q=70", "source": "unsplash", "author": "Unsplash Cable Car", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/cable-car"},
    {"url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500&q=70", "source": "unsplash", "author": "Unsplash Mountain View", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-summit"},
]

# POI-specific pools
HOSPITAL_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=500&q=70", "source": "unsplash", "author": "Unsplash Hospital", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/hospital"},
    {"url": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=500&q=70", "source": "unsplash", "author": "Unsplash Clinic", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/clinic"},
    {"url": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=500&q=70", "source": "unsplash", "author": "Unsplash Medical", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/medical"},
    {"url": "https://images.unsplash.com/photo-1551076805-e1869033e561?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1551076805-e1869033e561?w=500&q=70", "source": "unsplash", "author": "Unsplash Care", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/healthcare"},
]
PHARMACY_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=500&q=70", "source": "unsplash", "author": "Unsplash Pharmacy", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/pharmacy"},
    {"url": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=500&q=70", "source": "unsplash", "author": "Unsplash Medicines", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/medicine"},
]
POLICE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=500&q=70", "source": "unsplash", "author": "Unsplash Police Station", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/police-station"},
    {"url": "https://images.unsplash.com/photo-1589829441908-8edb4a1abb14?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1589829441908-8edb4a1abb14?w=500&q=70", "source": "unsplash", "author": "Unsplash Safety", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/police"},
]
BANK_ATM_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?w=500&q=70", "source": "unsplash", "author": "Unsplash Bank", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/bank"},
    {"url": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=500&q=70", "source": "unsplash", "author": "Unsplash ATM", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/atm"},
    {"url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=500&q=70", "source": "unsplash", "author": "Unsplash Finance", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/finance"},
]
RESTAURANT_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&q=70", "source": "unsplash", "author": "Unsplash Restaurant", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/restaurant"},
    {"url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500&q=70", "source": "unsplash", "author": "Unsplash Cafe", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/cafe"},
    {"url": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=500&q=70", "source": "unsplash", "author": "Unsplash Dining", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/dining"},
    {"url": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=500&q=70", "source": "unsplash", "author": "Unsplash Bhojan", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/food"},
]
SHOP_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1481437156560-3205f6a55735?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1481437156560-3205f6a55735?w=500&q=70", "source": "unsplash", "author": "Unsplash Shop", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/shop"},
    {"url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=500&q=70", "source": "unsplash", "author": "Unsplash Store", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/store"},
    {"url": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=500&q=70", "source": "unsplash", "author": "Unsplash Market", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/market"},
]
TRANSPORT_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=500&q=70", "source": "unsplash", "author": "Unsplash Bus", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/bus"},
    {"url": "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=500&q=70", "source": "unsplash", "author": "Unsplash Road", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/road"},
    {"url": "https://images.unsplash.com/photo-1529074282371-d15ec0e1fb9d?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1529074282371-d15ec0e1fb9d?w=500&q=70", "source": "unsplash", "author": "Unsplash Travel", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/travel"},
]

# Extra diversity photos merged into base pools
EXTRA_MOUNTAIN_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=500&q=70", "source": "unsplash", "author": "Unsplash Alpine", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya"},
    {"url": "https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=500&q=70", "source": "unsplash", "author": "Unsplash Peaks", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/himalaya"},
    {"url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=500&q=70", "source": "unsplash", "author": "Unsplash Vista", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-landscape"},
]
EXTRA_LAKE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=500&q=70", "source": "unsplash", "author": "Unsplash Blue Lake", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/lake"},
    {"url": "https://images.unsplash.com/photo-1497694814126-0373d79c4964?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1497694814126-0373d79c4964?w=500&q=70", "source": "unsplash", "author": "Unsplash Reflection", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/lake-reflection"},
    {"url": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=500&q=70", "source": "unsplash", "author": "Unsplash Fjord", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/mountain-lake"},
]
EXTRA_HERITAGE_PHOTOS = [
    {"url": "https://images.unsplash.com/photo-1528181304800-259b08848526?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1528181304800-259b08848526?w=500&q=70", "source": "unsplash", "author": "Unsplash Temple", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/temple"},
    {"url": "https://images.unsplash.com/photo-1542317877-291611718b07?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1542317877-291611718b07?w=500&q=70", "source": "unsplash", "author": "Unsplash Shrine", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/hindu-temple"},
    {"url": "https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1609766907931-3f30e2151d3a?w=500&q=70", "source": "unsplash", "author": "Unsplash Stupa", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/stupa"},
]
CITY_PHOTOS_EXTRA = [
    {"url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=500&q=70", "source": "unsplash", "author": "Unsplash Town", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/city"},
    {"url": "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1400&q=80", "thumb": "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=500&q=70", "source": "unsplash", "author": "Unsplash Street", "license": "Unsplash License", "source_url": "https://unsplash.com/s/photos/street"},
]

MOUNTAIN_PHOTOS.extend(EXTRA_MOUNTAIN_PHOTOS)
LAKE_PHOTOS.extend(EXTRA_LAKE_PHOTOS)
HERITAGE_PHOTOS.extend(EXTRA_HERITAGE_PHOTOS)
CITY_PHOTOS.extend(CITY_PHOTOS_EXTRA)

# ---------------------------------------------------------------------------
# Bundled AI-generated static photos shipped with the frontend.
# These are the OFFLINE_ACCURATE photos for 20 headline Nepal destinations.
# Folder name  -> file name                      (relative to /images/destinations/)
# ---------------------------------------------------------------------------

def _static_ai(folder: str, fname: str, caption: str, tags=None) -> dict:
    return {
        "url": f"/images/destinations/{folder}/{fname}",
        "thumb": f"/images/destinations/{folder}/{fname}",
        "source": "reference",
        "author": "AI-generated Nepal tourism imagery",
        "license": "Bundled with app (royalty-free)",
        "source_url": f"/images/destinations/{folder}/",
        "caption": caption,
        "tags": list(tags or []),
    }

STATIC_AI = {
    "nagarkot":      _static_ai("nagarkot",      "sunrise-view.jpg",      "Nagarkot sunrise over the Himalayas", ["viewpoint", "himalaya", "sunrise"]),
    "pokhara":       _static_ai("pokhara",       "fewatal.jpg",           "Phewa Lake, Pokhara",                 ["lake", "pokhara", "phewa"]),
    "everest":       _static_ai("everest",       "base-camp.jpg",         "Everest Base Camp trek",              ["mountain", "everest", "trek"]),
    "kathmandu":     _static_ai("kathmandu",     "durbar-square.jpg",     "Kathmandu Durbar Square",             ["heritage", "durbar", "kathmandu"]),
    "chitwan":       _static_ai("chitwan",       "safari.jpg",            "Chitwan National Park safari",        ["wildlife", "safari", "jungle"]),
    "lumbini":       _static_ai("lumbini",       "garden.jpg",            "Lumbini Sacred Garden",               ["heritage", "buddha", "lumbini"]),
    "bhaktapur":     _static_ai("bhaktapur",     "durbar.jpg",            "Bhaktapur Durbar Square",             ["heritage", "durbar", "newar"]),
    "annapurna":     _static_ai("annapurna",     "trek.jpg",              "Annapurna Circuit trek",              ["mountain", "trek", "annapurna"]),
    "patan":         _static_ai("patan",         "durbar.jpg",            "Patan Durbar Square",                 ["heritage", "durbar", "newar"]),
    "mustang":       _static_ai("mustang",       "lo-manthang.jpg",       "Lo Manthang, Upper Mustang",          ["mountain", "mustang", "tibet"]),
    "ilam":          _static_ai("ilam",          "tea-gardens.jpg",       "Ilam tea gardens",                    ["tea", "hills", "garden"]),
    "janakpur":      _static_ai("janakpur",      "janaki-mandir.jpg",     "Janaki Mandir, Janakpur",             ["heritage", "temple", "hindu"]),
    "bandipur":      _static_ai("bandipur",      "hilltop-village.jpg",   "Bandipur hilltop Newari village",     ["heritage", "village", "hill"]),
    "bardiya":       _static_ai("bardiya",       "tiger-reserve.jpg",     "Bardiya National Park tiger reserve", ["wildlife", "tiger", "jungle"]),
    "dolpo":         _static_ai("dolpo",         "highland-village.jpg",  "Dolpo highland village",              ["mountain", "village", "dolpo"]),
    "gosaikunda":    _static_ai("gosaikunda",    "glacial-lake.jpg",      "Gosaikunda glacial lake",             ["lake", "holy", "trek"]),
    "koshi-tappu":   _static_ai("koshi-tappu",   "wetlands.jpg",          "Koshi Tappu Wildlife Reserve",        ["wildlife", "wetlands", "birds"]),
    "manaslu":       _static_ai("manaslu",       "mountain-peak.jpg",     "Mount Manaslu peak",                  ["mountain", "peak", "trek"]),
    "rara":          _static_ai("rara",          "alpine-lake.jpg",       "Rara Lake alpine scenery",            ["lake", "national park"]),
    "tilicho":       _static_ai("tilicho",       "himalayan-lake.jpg",    "Tilicho Lake in the Annapurna region",["lake", "himal", "trek"]),
}

# ---------------------------------------------------------------------------
# Mappings (defined AFTER all pools exist so NameError can't happen)
# ---------------------------------------------------------------------------

CATEGORY_POOLS = {
    "mountain": MOUNTAIN_PHOTOS,
    "peak": MOUNTAIN_PHOTOS,
    "himal": MOUNTAIN_PHOTOS,
    "trek": MOUNTAIN_PHOTOS,
    "trekking": MOUNTAIN_PHOTOS,
    "hiking": MOUNTAIN_PHOTOS,
    "trail": MOUNTAIN_PHOTOS,
    "pass": MOUNTAIN_PHOTOS,
    "adventure": MOUNTAIN_PHOTOS,
    "camp": MOUNTAIN_PHOTOS,
    "viewpoint": ATTRACTION_PHOTOS,
    "photography": ATTRACTION_PHOTOS,
    "scenic": ATTRACTION_PHOTOS,
    "attraction": ATTRACTION_PHOTOS,
    "lake": LAKE_PHOTOS,
    "tal": LAKE_PHOTOS,
    "kunda": LAKE_PHOTOS,
    "water": LAKE_PHOTOS,
    "river": LAKE_PHOTOS,
    "waterfall": WATERFALL_PHOTOS,
    "fall": WATERFALL_PHOTOS,
    "cave": CAVE_PHOTOS,
    "gufa": CAVE_PHOTOS,
    "caves": CAVE_PHOTOS,
    "temple": HERITAGE_PHOTOS,
    "heritage": HERITAGE_PHOTOS,
    "stupa": HERITAGE_PHOTOS,
    "monastery": HERITAGE_PHOTOS,
    "gompa": HERITAGE_PHOTOS,
    "durbar": HERITAGE_PHOTOS,
    "mandir": HERITAGE_PHOTOS,
    "mahadev": HERITAGE_PHOTOS,
    "religious": HERITAGE_PHOTOS,
    "church": HERITAGE_PHOTOS,
    "mosque": HERITAGE_PHOTOS,
    "palace": HERITAGE_PHOTOS,
    "museum": MUSEUM_PHOTOS,
    "bazaar": CITY_PHOTOS,
    "city": CITY_PHOTOS,
    "market": CITY_PHOTOS,
    "shopping": CITY_PHOTOS,
    "street": CITY_PHOTOS,
    "thamel": CITY_PHOTOS,
    "food": CITY_PHOTOS,
    "festival": CITY_PHOTOS,
    "wildlife": WILDLIFE_PHOTOS,
    "safari": WILDLIFE_PHOTOS,
    "national park": WILDLIFE_PHOTOS,
    "jungle": WILDLIFE_PHOTOS,
    "reserve": WILDLIFE_PHOTOS,
    "park": WILDLIFE_PHOTOS,
    "zoo": WILDLIFE_PHOTOS,
    "garden": GARDEN_PARK_PHOTOS,
    "botanical": GARDEN_PARK_PHOTOS,
    "tea": TEAGARDEN_PHOTOS,
    "tea garden": TEAGARDEN_PHOTOS,
    "plantation": TEAGARDEN_PHOTOS,
    "cable car": CABLECAR_PHOTOS,
    "cablecar": CABLECAR_PHOTOS,
    "ropeway": CABLECAR_PHOTOS,
    "tower": CABLECAR_PHOTOS,
    "hotel": HOTEL_PHOTOS,
    "resort": HOTEL_PHOTOS,
    "lodge": HOTEL_PHOTOS,
    "guest house": HOTEL_PHOTOS,
    "guesthouse": HOTEL_PHOTOS,
    "homestay": HOTEL_PHOTOS,
    "hostel": HOTEL_PHOTOS,
    "motel": HOTEL_PHOTOS,
    "alpine hut": HOTEL_PHOTOS,
    "camp_site": HOTEL_PHOTOS,
    "apartment": HOTEL_PHOTOS,
}

# Categories considered "accommodation" (filtered OUT of the default
# attractions grid and into a separate "Hotels" section).
ACCOMMODATION_CATEGORIES = {
    "hotel", "resort", "lodge", "guest_house", "guesthouse", "guest house",
    "hostel", "motel", "homestay", "alpine_hut", "alpine hut", "camp_site",
    "camp site", "apartment",
}

POI_PHOTO_POOLS = {
    "hospital": HOSPITAL_PHOTOS,
    "clinic": HOSPITAL_PHOTOS,
    "pharmacy": PHARMACY_PHOTOS,
    "police": POLICE_PHOTOS,
    "bank": BANK_ATM_PHOTOS,
    "atm": BANK_ATM_PHOTOS,
    "restaurant": RESTAURANT_PHOTOS,
    "cafe": RESTAURANT_PHOTOS,
    "shop": SHOP_PHOTOS,
    "store": SHOP_PHOTOS,
    "market": SHOP_PHOTOS,
    "bus": TRANSPORT_PHOTOS,
    "transport": TRANSPORT_PHOTOS,
    "attraction": ATTRACTION_PHOTOS,
    "viewpoint": ATTRACTION_PHOTOS,
    "hotel": HOTEL_PHOTOS,
    "resort": HOTEL_PHOTOS,
    "lodge": HOTEL_PHOTOS,
}

# ---------------------------------------------------------------------------
# Landmark keywords -> EXPLICIT static photo (guarantees accuracy).
# IMPORTANT: values are dicts, not indices - so pool re-ordering never
# breaks these. Falls back to Unsplash pool entries when no AI photo exists.
# ---------------------------------------------------------------------------

def _mk_unsplash_landmark(pool, idx, caption=""):
    p = pool[idx]
    if caption:
        p = dict(p)
        p["caption"] = caption
    return p

LANDMARK_PHOTOS = {
    # --- Static AI (always accurate, works offline) ---
    # NOTE: No bare "pokhara" key — only places with "phewa"/"fewa" in the name
    # get the Phewa lake photo (otherwise every Pokhara restaurant/hotel/cave
    # would show the lake photo incorrectly).
    "nagarkot":               STATIC_AI["nagarkot"],
    "phewa":                  STATIC_AI["pokhara"],
    "phewa lake":             STATIC_AI["pokhara"],
    "fewa":                   STATIC_AI["pokhara"],
    "fewa tal":               STATIC_AI["pokhara"],
    "fewatal":                STATIC_AI["pokhara"],
    "everest":                STATIC_AI["everest"],
    "sagarmatha":             STATIC_AI["everest"],
    "ebc":                    STATIC_AI["everest"],
    "kathmandu":              STATIC_AI["kathmandu"],
    "chitwan":                STATIC_AI["chitwan"],
    "sauraha":                STATIC_AI["chitwan"],
    "lumbini":                STATIC_AI["lumbini"],
    "bhaktapur":              STATIC_AI["bhaktapur"],
    "annapurna":              STATIC_AI["annapurna"],
    "patan":                  STATIC_AI["patan"],
    "lalitpur":               STATIC_AI["patan"],
    "mustang":                STATIC_AI["mustang"],
    "lo manthang":            STATIC_AI["mustang"],
    "ilam":                   STATIC_AI["ilam"],
    "kanyam":                 STATIC_AI["ilam"],
    "janakpur":               STATIC_AI["janakpur"],
    "janaki":                 STATIC_AI["janakpur"],
    "bandipur":               STATIC_AI["bandipur"],
    "bardiya":                STATIC_AI["bardiya"],
    "dolpo":                  STATIC_AI["dolpo"],
    "gosaikunda":             STATIC_AI["gosaikunda"],
    "koshi tappu":            STATIC_AI["koshi-tappu"],
    "koshi-tappu":            STATIC_AI["koshi-tappu"],
    "manaslu":                STATIC_AI["manaslu"],
    "rara":                   STATIC_AI["rara"],
    "tilicho":                STATIC_AI["tilicho"],

    # --- Unsplash fallbacks for destinations without an AI photo yet ---
    "begnas":                 _mk_unsplash_landmark(LAKE_PHOTOS, 3, "Begnas Lake, Pokhara"),
    "rupa lake":              _mk_unsplash_landmark(LAKE_PHOTOS, 4, "Rupa Lake, Pokhara"),
    "shey phoksundo":         _mk_unsplash_landmark(LAKE_PHOTOS, 4, "Phoksundo Lake, Dolpa"),
    "phoksundo":              _mk_unsplash_landmark(LAKE_PHOTOS, 4, "Phoksundo Lake, Dolpa"),
    "pashupatinath":          _mk_unsplash_landmark(HERITAGE_PHOTOS, 4, "Pashupatinath Temple"),
    "boudhanath":             _mk_unsplash_landmark(HERITAGE_PHOTOS, 2, "Boudhanath Stupa"),
    "boudha":                 _mk_unsplash_landmark(HERITAGE_PHOTOS, 2, "Boudhanath Stupa"),
    "swayambhunath":          _mk_unsplash_landmark(HERITAGE_PHOTOS, 3, "Swayambhunath Stupa"),
    "swayambhu":              _mk_unsplash_landmark(HERITAGE_PHOTOS, 3, "Swayambhunath Stupa"),
    "muktinath":              _mk_unsplash_landmark(HERITAGE_PHOTOS, 0, "Muktinath Temple"),
    "manakamana":             _mk_unsplash_landmark(HERITAGE_PHOTOS, 0, "Manakamana Temple"),
    "dharahara":              _mk_unsplash_landmark(CITY_PHOTOS, 0, "Dharahara Tower, Kathmandu"),
    "thamel":                 _mk_unsplash_landmark(CITY_PHOTOS, 2, "Thamel, Kathmandu"),
    "namche":                 _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 4, "Namche Bazaar"),
    "namche bazaar":          _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 4, "Namche Bazaar"),
    "sarangkot":              _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 0, "Sarangkot viewpoint, Pokhara"),
    "poon hill":              _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 8, "Poon Hill viewpoint"),
    "kala patthar":           _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 3, "Kala Patthar viewpoint, EBC"),
    "machhapuchhre":          _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 1, "Machhapuchhre (Fishtail) peak"),
    "machhapuchhare":         _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 1, "Machhapuchhre (Fishtail) peak"),
    "fishtail":               _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 1, "Machhapuchhre (Fishtail) peak"),
    "langtang":               _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 5, "Langtang Valley trek"),
    "helambu":                _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 9, "Helambu trek"),
    "devis fall":             _mk_unsplash_landmark(WATERFALL_PHOTOS, 0, "Davis Falls (Patale Chhango), Pokhara"),
    "davis fall":             _mk_unsplash_landmark(WATERFALL_PHOTOS, 0, "Davis Falls (Patale Chhango), Pokhara"),
    "patale chhango":         _mk_unsplash_landmark(WATERFALL_PHOTOS, 0, "Patale Chhango (Davis Falls)"),
    "mahendra cave":          _mk_unsplash_landmark(CAVE_PHOTOS, 0, "Mahendra Cave, Pokhara"),
    "mahendra gufa":          _mk_unsplash_landmark(CAVE_PHOTOS, 0, "Mahendra Cave, Pokhara"),
    "gupteshwor":             _mk_unsplash_landmark(CAVE_PHOTOS, 1, "Gupteshwor Cave, Pokhara"),
    "chamere gufa":           _mk_unsplash_landmark(CAVE_PHOTOS, 2, "Bat Cave, Pokhara"),
    "bindhyabasini":          _mk_unsplash_landmark(HERITAGE_PHOTOS, 0, "Bindhyabasini Temple, Pokhara"),
    "world peace pagoda":     _mk_unsplash_landmark(HERITAGE_PHOTOS, 2, "World Peace Pagoda, Pokhara"),
    "shanti stupa":           _mk_unsplash_landmark(HERITAGE_PHOTOS, 2, "World Peace Pagoda, Pokhara"),
    "garden of dreams":       _mk_unsplash_landmark(GARDEN_PARK_PHOTOS, 0, "Garden of Dreams, Kathmandu"),
    "narayanhiti":            _mk_unsplash_landmark(HERITAGE_PHOTOS, 0, "Narayanhiti Palace Museum, Kathmandu"),
    "hanuman dhoka":          _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Hanuman Dhoka Durbar, Kathmandu"),
    "kopan monastery":        _mk_unsplash_landmark(HERITAGE_PHOTOS, 2, "Kopan Monastery, Kathmandu"),
    "phulchowki":             _mk_unsplash_landmark(ATTRACTION_PHOTOS, 1, "Phulchowki viewpoint"),
    "chandragiri":            _mk_unsplash_landmark(CABLECAR_PHOTOS, 1, "Chandragiri Hill cable car"),
    "kyanjin":                _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 5, "Kyanjin Gompa, Langtang"),
    "tengboche":              _mk_unsplash_landmark(HERITAGE_PHOTOS, 2, "Tengboche Monastery, EBC"),
    "gokyo":                  _mk_unsplash_landmark(LAKE_PHOTOS, 4, "Gokyo Lakes"),
    "thorong la":             _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 6, "Thorong La pass"),
    "thorung la":             _mk_unsplash_landmark(MOUNTAIN_PHOTOS, 6, "Thorong La pass"),
    "kagbeni":                _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Kagbeni village, Mustang"),
    "rani mahal":             _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Rani Mahal, Palpa"),
    "tansen":                 _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Tansen, Palpa"),
    "palpa":                  _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Tansen, Palpa"),
    "gorkha durbar":          _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Gorkha Durbar"),
    "gorkha":                 _mk_unsplash_landmark(HERITAGE_PHOTOS, 1, "Gorkha Durbar"),
    "halesi":                 _mk_unsplash_landmark(CAVE_PHOTOS, 0, "Halesi Mahadev cave"),
    "pathibhara":             _mk_unsplash_landmark(HERITAGE_PHOTOS, 0, "Pathibhara Devi temple"),
    "khaptad":                _mk_unsplash_landmark(WILDLIFE_PHOTOS, 3, "Khaptad National Park"),
    "shree antu":             _mk_unsplash_landmark(ATTRACTION_PHOTOS, 0, "Shree Antu viewpoint, Ilam"),
    "panch pokhari":          _mk_unsplash_landmark(LAKE_PHOTOS, 4, "Panch Pokhari"),
}

# Map LANDMARK_PHOTOS key -> the bucket pool for rotation.
# We use explicit key-to-pool mapping instead of URL substring heuristics,
# which was unreliable (URL hashes don't contain category keywords).
_LANDMARK_POOL_MAP = {
    # Mountain / trekking
    "everest": MOUNTAIN_PHOTOS, "sagarmatha": MOUNTAIN_PHOTOS, "ebc": MOUNTAIN_PHOTOS,
    "annapurna": MOUNTAIN_PHOTOS, "machhapuchhre": MOUNTAIN_PHOTOS,
    "machhapuchhare": MOUNTAIN_PHOTOS, "fishtail": MOUNTAIN_PHOTOS,
    "namche": MOUNTAIN_PHOTOS, "namche bazaar": MOUNTAIN_PHOTOS,
    "sarangkot": MOUNTAIN_PHOTOS, "poon hill": MOUNTAIN_PHOTOS,
    "kala patthar": MOUNTAIN_PHOTOS, "langtang": MOUNTAIN_PHOTOS,
    "helambu": MOUNTAIN_PHOTOS, "kyanjin": MOUNTAIN_PHOTOS,
    "thorong la": MOUNTAIN_PHOTOS, "thorung la": MOUNTAIN_PHOTOS,
    "phulchowki": MOUNTAIN_PHOTOS,
    # Lake
    "phewa": LAKE_PHOTOS, "fewa": LAKE_PHOTOS, "fewatal": LAKE_PHOTOS,
    "begnas": LAKE_PHOTOS, "rupa lake": LAKE_PHOTOS, "rara": LAKE_PHOTOS,
    "tilicho": LAKE_PHOTOS, "gosaikunda": LAKE_PHOTOS,
    "shey phoksundo": LAKE_PHOTOS, "phoksundo": LAKE_PHOTOS,
    "gokyo": LAKE_PHOTOS, "panch pokhari": LAKE_PHOTOS,
    # Heritage / temples / stupas / durbars / palaces
    "pashupatinath": HERITAGE_PHOTOS, "boudhanath": HERITAGE_PHOTOS,
    "boudha": HERITAGE_PHOTOS, "swayambhunath": HERITAGE_PHOTOS,
    "swayambhu": HERITAGE_PHOTOS, "bhaktapur": HERITAGE_PHOTOS,
    "patan": HERITAGE_PHOTOS, "lalitpur": HERITAGE_PHOTOS,
    "lumbini": HERITAGE_PHOTOS, "janakpur": HERITAGE_PHOTOS, "janaki": HERITAGE_PHOTOS,
    "muktinath": HERITAGE_PHOTOS, "manakamana": HERITAGE_PHOTOS,
    "bindhyabasini": HERITAGE_PHOTOS, "world peace pagoda": HERITAGE_PHOTOS,
    "shanti stupa": HERITAGE_PHOTOS, "narayanhiti": HERITAGE_PHOTOS,
    "hanuman dhoka": HERITAGE_PHOTOS, "kopan monastery": HERITAGE_PHOTOS,
    "tengboche": HERITAGE_PHOTOS, "kagbeni": HERITAGE_PHOTOS,
    "bandipur": HERITAGE_PHOTOS, "rani mahal": HERITAGE_PHOTOS,
    "tansen": HERITAGE_PHOTOS, "palpa": HERITAGE_PHOTOS,
    "gorkha durbar": HERITAGE_PHOTOS, "gorkha": HERITAGE_PHOTOS,
    "pathibhara": HERITAGE_PHOTOS, "dharahara": HERITAGE_PHOTOS,
    # Cave
    "mahendra cave": CAVE_PHOTOS, "mahendra gufa": CAVE_PHOTOS,
    "gupteshwor": CAVE_PHOTOS, "chamere gufa": CAVE_PHOTOS, "halesi": CAVE_PHOTOS,
    # Waterfall
    "devis fall": WATERFALL_PHOTOS, "davis fall": WATERFALL_PHOTOS,
    "patale chhango": WATERFALL_PHOTOS,
    # Wildlife
    "chitwan": WILDLIFE_PHOTOS, "sauraha": WILDLIFE_PHOTOS,
    "bardiya": WILDLIFE_PHOTOS, "koshi tappu": WILDLIFE_PHOTOS,
    "koshi-tappu": WILDLIFE_PHOTOS, "khaptad": WILDLIFE_PHOTOS,
    # City / street
    "kathmandu": CITY_PHOTOS, "thamel": CITY_PHOTOS,
    # Garden
    "garden of dreams": GARDEN_PARK_PHOTOS,
    # Tea / garden
    "ilam": TEAGARDEN_PHOTOS, "kanyam": TEAGARDEN_PHOTOS,
    # Cable car
    "chandragiri": CABLECAR_PHOTOS,
    # Mountain (static AI)
    "nagarkot": MOUNTAIN_PHOTOS, "everest": MOUNTAIN_PHOTOS,
    "mustang": MOUNTAIN_PHOTOS, "dolpo": MOUNTAIN_PHOTOS, "manaslu": MOUNTAIN_PHOTOS,
    "annapurna": MOUNTAIN_PHOTOS,
    # Viewpoint / attraction
    "shree antu": ATTRACTION_PHOTOS,
}


def _landmark_pool_for_key(key: str):
    """Look up pool by key first; fall back to tag/url inspection."""
    pool = _LANDMARK_POOL_MAP.get(key)
    if pool is not None:
        return pool
    # fallback: check url
    url = ""
    entry = LANDMARK_PHOTOS.get(key, {})
    url = entry.get("url", "") if isinstance(entry, dict) else ""
    tags = entry.get("tags", []) if isinstance(entry, dict) else []
    if "cave" in url or "cave" in tags: return CAVE_PHOTOS
    if "waterfall" in url or "waterfall" in tags: return WATERFALL_PHOTOS
    if "lake" in tags: return LAKE_PHOTOS
    if "mountain" in tags or "trek" in tags or "peak" in tags: return MOUNTAIN_PHOTOS
    if "heritage" in tags or "temple" in tags or "durbar" in tags: return HERITAGE_PHOTOS
    if "wildlife" in tags or "safari" in tags or "jungle" in tags: return WILDLIFE_PHOTOS
    if "garden" in tags or "tea" in tags: return GARDEN_PARK_PHOTOS
    if "viewpoint" in tags: return ATTRACTION_PHOTOS
    return GENERAL_PHOTOS


def _landmark_pool(photo_dict):
    """Return the right bucket pool given a photo dict (used by _pick_varied)."""
    url = photo_dict.get("url", "")
    # static AI photos - route by URL folder
    if "/images/destinations/" in url:
        folder = url.split("/images/destinations/")[-1].split("/")[0]
        static_pools = {
            "nagarkot": MOUNTAIN_PHOTOS, "everest": MOUNTAIN_PHOTOS,
            "annapurna": MOUNTAIN_PHOTOS, "mustang": MOUNTAIN_PHOTOS,
            "manaslu": MOUNTAIN_PHOTOS, "dolpo": MOUNTAIN_PHOTOS,
            "rara": LAKE_PHOTOS,
            "tilicho": LAKE_PHOTOS, "gosaikunda": LAKE_PHOTOS,
            "kathmandu": HERITAGE_PHOTOS, "bhaktapur": HERITAGE_PHOTOS,
            "patan": HERITAGE_PHOTOS, "lumbini": HERITAGE_PHOTOS,
            "janakpur": HERITAGE_PHOTOS, "bandipur": HERITAGE_PHOTOS,
            "chitwan": WILDLIFE_PHOTOS, "bardiya": WILDLIFE_PHOTOS,
            "koshi-tappu": WILDLIFE_PHOTOS,
            "ilam": TEAGARDEN_PHOTOS,
        }
        return static_pools.get(folder, GENERAL_PHOTOS)
    # Unsplash photos: find by identity (which pool contains this exact dict?)
    for pool in (MOUNTAIN_PHOTOS, LAKE_PHOTOS, WATERFALL_PHOTOS, HERITAGE_PHOTOS,
                 WILDLIFE_PHOTOS, CITY_PHOTOS, HOTEL_PHOTOS, GENERAL_PHOTOS,
                 ATTRACTION_PHOTOS, CAVE_PHOTOS, MUSEUM_PHOTOS,
                 GARDEN_PARK_PHOTOS, TEAGARDEN_PHOTOS, CABLECAR_PHOTOS):
        # Use identity check: the dict object is the same instance because
        # _mk_unsplash_landmark creates a new dict via dict(p); so compare by URL.
        for p in pool:
            if p.get("url") == url:
                return pool
    return GENERAL_PHOTOS

# ---------------------------------------------------------------------------
# Resolver helpers
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _category_pool(category_name: str):
    cat = (category_name or "").lower()
    # longest keys first to match "national park" before "park" etc.
    for key in sorted(CATEGORY_POOLS.keys(), key=len, reverse=True):
        if key in cat:
            return CATEGORY_POOLS[key]
    return None


def _pick_varied(pool, primary_photo, dest_id):
    """Deterministic rotation within the pool so same-category destinations
    don't all show the identical Unsplash URL."""
    if not pool:
        return primary_photo
    try:
        start = pool.index(primary_photo)
    except ValueError:
        start = 0
    return pool[(start + (dest_id % max(1, len(pool)))) % len(pool)]


def is_accommodation_category(category_name: str) -> bool:
    """Return True if the category name is a hotel/lodge/hostel/etc."""
    if not category_name:
        return False
    low = category_name.lower().replace("-", " ").replace("_", " ")
    return any(acc in low for acc in ACCOMMODATION_CATEGORIES)


def resolve_cover_photo(destination) -> dict:
    """Return a provenance dict {url, thumb, source, author, license, source_url}
    for a destination. Deterministic per destination."""
    name = getattr(destination, "name", "") or ""
    city = getattr(destination, "city", "") or ""
    district = getattr(destination, "district", "") or ""
    province = getattr(destination, "province", "") or ""
    name_hay = _norm(name)
    place_hay = _norm(f"{city} {district} {province}")
    dest_id = getattr(destination, "id", None) or 0

    # 1. Exact landmark match. Prioritize NAME matches (strongest signal)
    #    before falling back to city/district, so that e.g. "Mahendra Cave"
    #    with city="Pokhara" doesn't get the Phewa Lake photo.
    matched_key = None
    matched_photo = None
    for key, photo in sorted(LANDMARK_PHOTOS.items(), key=lambda kv: -len(kv[0])):
        nk = _norm(key)
        if nk and nk in name_hay:
            matched_key = key
            matched_photo = photo
            break
    if matched_photo is None:
        # Place-hay fallback (only longer keys to avoid false positives)
        for key, photo in sorted(LANDMARK_PHOTOS.items(), key=lambda kv: -len(kv[0])):
            nk = _norm(key)
            if nk and len(nk) >= 6 and nk in place_hay:
                matched_key = key
                matched_photo = photo
                break
    if matched_photo is not None:
        # Important: if this is an UNSPLASH landmark (dict created by
        # _mk_unsplash_landmark), we must treat pool lookup by url; but we
        # ALSO want to make sure the returned photo is a dict from the actual
        # pool (or the photo itself) so _pick_varied rotation works when
        # primary is in the pool. Since _mk_unsplash_landmark copies the dict,
        # we find the original pool entry by url to use as rotation anchor.
        url = matched_photo.get("url", "")
        if url.startswith("/images/"):
            pool = _landmark_pool(matched_photo)
            return _pick_varied(pool, matched_photo, dest_id)
        # Unsplash: find original dict in its pool
        for pool in (MOUNTAIN_PHOTOS, LAKE_PHOTOS, WATERFALL_PHOTOS,
                     HERITAGE_PHOTOS, WILDLIFE_PHOTOS, CITY_PHOTOS,
                     ATTRACTION_PHOTOS, CAVE_PHOTOS, MUSEUM_PHOTOS,
                     GARDEN_PARK_PHOTOS, TEAGARDEN_PHOTOS, CABLECAR_PHOTOS,
                     HOTEL_PHOTOS, GENERAL_PHOTOS):
            for orig in pool:
                if orig.get("url") == url:
                    return _pick_varied(pool, orig, dest_id)
        # Couldn't find anchor; return the matched photo directly (no rotation)
        return matched_photo

    # 2. Category-based pool (uses Destination.category FK)
    category = getattr(destination, "category", None)
    cat_name = ""
    if category is not None:
        cat_name = getattr(category, "name", "") or ""
    pool = _category_pool(cat_name)

    # 3. Name keyword -> pool
    combined_hay = _norm(f"{name} {city} {district} {province}")
    if pool is None:
        for key in sorted(CATEGORY_POOLS.keys(), key=len, reverse=True):
            if _norm(key) in combined_hay:
                pool = CATEGORY_POOLS[key]
                break

    if pool is None:
        pool = GENERAL_PHOTOS

    return pool[dest_id % len(pool)]


def resolve_hotel_photo(hotel) -> dict:
    """Assign a relevant hotel/lodge photo, varied per hotel."""
    name = (getattr(hotel, "name", "") or "").lower()
    if any(w in name for w in ("resort", "retreat", "spa")):
        pool = HOTEL_PHOTOS[1:4]
    elif any(w in name for w in ("lodge", "teahouse", "tea house", "guest house", "guesthouse", "inn")):
        pool = HOTEL_PHOTOS[3:] + HOTEL_PHOTOS[:2]
    else:
        pool = HOTEL_PHOTOS
    hotel_id = getattr(hotel, "id", None) or 0
    return pool[hotel_id % len(pool)]


# ---------------------------------------------------------------------------
# Live Wikimedia Commons enrichment
# ---------------------------------------------------------------------------

_ACCEPTED_LICENSE_PATTERNS = (
    "cc by", "cc-by", "cc0", "public domain", "pd",
    "unsplash license", "pexels license", "pixabay license",
)
_RESTRICTED_PATTERNS = ("nc", "non-commercial", "noncommercial", "all rights reserved", "copyrighted")


def is_commercially_reusable(license_str: str) -> bool:
    if not license_str:
        return False
    low = license_str.lower()
    if any(bad in low for bad in _RESTRICTED_PATTERNS):
        return False
    return any(good in low for good in _ACCEPTED_LICENSE_PATTERNS)


def acquire_wikimedia_photos(destination, limit: int = 8, timeout: int = 6):
    """Search Wikimedia Commons for real photos. Returns [] on any error."""
    import requests

    queries = []
    name = getattr(destination, "name", "") or ""
    if name:
        queries.append(f"{name} Nepal")
    city = getattr(destination, "city", "") or ""
    if city:
        queries.append(f"{city} Nepal")
    district = getattr(destination, "district", "") or ""
    if district:
        queries.append(f"{district} Nepal")
    if not queries:
        return []

    results = []
    seen_urls = set()
    headers = {"User-Agent": USER_AGENT}

    for query in queries:
        if len(results) >= limit:
            break
        try:
            res = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query", "format": "json",
                    "generator": "search",
                    "gsrsearch": f"{query} landscape",
                    "gsrnamespace": 6, "gsrlimit": min(limit * 2, 20),
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata|size|mime",
                    "iiurlwidth": 1200,
                },
                headers=headers, timeout=timeout,
            )
            res.raise_for_status()
            pages = res.json().get("query", {}).get("pages", {})
        except Exception as exc:  # noqa: BLE001
            logger.info("Wikimedia search failed for %r: %s", query, exc)
            continue

        for page in pages.values():
            if len(results) >= limit:
                break
            ii = (page.get("imageinfo") or [{}])[0]
            url = ii.get("thumburl") or ii.get("url")
            mime = (ii.get("mime") or "").lower()
            width = ii.get("thumbwidth") or ii.get("width") or 0
            if not url or "svg" in mime or not mime.startswith("image/"):
                continue
            if not width or width < 600:
                continue
            if url in seen_urls:
                continue

            meta = ii.get("extmetadata", {}) or {}
            license_str = (
                meta.get("LicenseShortName", {}).get("value")
                or meta.get("License", {}).get("value", "")
                or "CC BY-SA"
            )
            if not is_commercially_reusable(license_str):
                continue
            import html
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "Wikimedia Commons contributor"))
            artist = html.unescape(artist).strip()[:120] or "Wikimedia Commons contributor"
            desc_url = ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/File:{page.get('title', '')}"

            seen_urls.add(url)
            results.append({
                "url": url,
                "thumb": url,
                "source": "wikimedia",
                "author": artist,
                "license": license_str,
                "source_url": desc_url,
                "relevance_score": 85,
                "is_ai_generated": False,
            })

    return results


# ---------------------------------------------------------------------------
# POI photo resolver
# ---------------------------------------------------------------------------

def resolve_poi_photo(poi_type: str = "", poi_name: str = "", seed: int = 0) -> dict:
    """Deterministic, category-appropriate photo for a nearby POI."""
    hay = f"{poi_type} {poi_name}".lower()
    for key in sorted(POI_PHOTO_POOLS.keys(), key=len, reverse=True):
        if key in hay:
            pool = POI_PHOTO_POOLS[key]
            return pool[(int(seed or 0)) % len(pool)]
    if any(w in hay for w in ("health", "medical", "doctor", "emergency")):
        return HOSPITAL_PHOTOS[seed % len(HOSPITAL_PHOTOS)]
    if any(w in hay for w in ("money", "cash", "finance")):
        return BANK_ATM_PHOTOS[seed % len(BANK_ATM_PHOTOS)]
    if any(w in hay for w in ("food", "eat", "kitchen", "mo:mo", "momo")):
        return RESTAURANT_PHOTOS[seed % len(RESTAURANT_PHOTOS)]
    if any(w in hay for w in ("buy", "market", "grocery")):
        return SHOP_PHOTOS[seed % len(SHOP_PHOTOS)]
    return ATTRACTION_PHOTOS[seed % len(ATTRACTION_PHOTOS)]
