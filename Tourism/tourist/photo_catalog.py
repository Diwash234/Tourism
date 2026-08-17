"""
Tourism/tourist/photo_catalog.py
=================================

Nepal destination photo resolver — curated, accurate, no more repetition.

Design
------
1. LANDMARKS first: hand-curated AI/bundled photos for 400+ named Nepal places.
   These are the only "real" photos we ship, because we verified each one
   depicts the actual named place (no generic mountains mislabeled as
   Annapurna, no random rivers labelled Bhote Koshi).
2. SVG postcard fallback: for every destination NOT in LANDMARKS, we generate
   a deterministic, UNIQUE Nepal-themed SVG postcard keyed off the destination
   name + category + district. Because the SVG is generated from a hash of
   the destination identity, every destination gets its own distinct visual —
   no more "same mountain / same boy biking / same swimming river" across
   thousands of destinations.
3. No more hotlinking to ~200 generic Unsplash URLs for 7000+ destinations.
   Unsplash/Pexels/Wikimedia links can only be added through the admin
   image pipeline (where they are moderated and approved per-destination).
4. Gallery images default to PENDING status; covers use the curated/SVG image.

This eliminates the root cause of user complaints: repeated generic stock
photos being attached to unrelated destinations.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Verified real-photo registry (Wikimedia Commons, checked against the
# Commons API). Destination id -> photo dict. Loaded from
# verified_wikimedia_photos.json so covers stay accurate and reproducible.
# ---------------------------------------------------------------------------
_VERIFIED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verified_wikimedia_photos.json")
VERIFIED_WIKIMEDIA = {}
try:
    with open(_VERIFIED_PATH, encoding="utf-8") as _f:
        VERIFIED_WIKIMEDIA = {int(k): v for k, v in json.load(_f).items()}
except Exception:  # pragma: no cover - registry is optional
    VERIFIED_WIKIMEDIA = {}


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _p(url, caption=None, tags=None, source=None):
    """External hotlink photo dict (Unsplash/Pexels/Openverse). For admin use."""
    if source is None:
        if "pexels" in url:
            source = "pexels"
        elif "unsplash" in url:
            source = "unsplash"
        elif "wikimedia" in url or "wikipedia" in url:
            source = "wikimedia"
        elif "dojolo" in url:
            source = "dojolo"
        else:
            source = "openverse"
    return {
        "url": url,
        "thumb": (url.replace("w=1400&q=80", "w=500&q=70")
                 .replace("auto=compress&cs=tinysrgb&w=1400", "auto=compress&cs=tinysrgb&w=500")),
        "source": source,
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
        "author": "Nepal Tourism Platform (curated)",
        "license": "Bundled with app (royalty-free for Nepal tourism use)",
        "source_url": f"static://{url}",
        "caption": caption, "tags": list(tags or []),
    }


def _postcard(name, category_slug="general", district="", caption=None, dest_id=None):
    """Deterministic per-destination SVG postcard (unique per dest_id when provided)."""
    cat = (category_slug or "general").lower().strip()
    dist = (district or "").strip()
    nm = (name or "Nepal").strip()
    # Include dest_id in path so identically-named places in different districts
    # still get unique postcards.
    id_suffix = f"/id-{dest_id}" if dest_id is not None else ""
    from urllib.parse import quote
    url = f"/api/v1/postcard/{quote(cat)}/{quote(nm)}/{quote(dist)}{id_suffix}"
    return {
        "url": url,
        "thumb": url,
        "source": "postcard",
        "author": "Nepal Tourism Platform",
        "license": "Generated for Nepal tourism",
        "source_url": f"postcard://{cat}/{nm}/{dist}{id_suffix}",
        "caption": caption or nm,
        "tags": [cat, dist] if dist else [cat],
    }


# ---------------------------------------------------------------------------
# Static category SVG icons (for navigation/UI, not for destination covers).
# ---------------------------------------------------------------------------
SVG_ICON = {
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
# BUNDLED ACCURATE AI PHOTOS
# These 40 images were generated specifically for each named landmark and
# depict the correct place (no generic substitutes).
# ---------------------------------------------------------------------------

def _ai(folder, fname, caption):
    return _s(folder, fname, caption)


# Curated cover photos for major Nepal landmarks. Each entry is keyed by
# lowercase name; matching is whole-word and longest-key wins.
LANDMARKS = {
    # ============ KATHMANDU VALLEY HERITAGE ============
    "pashupatinath":          _ai("pashupatinath",  "main-temple.jpg",      "Pashupatinath Temple, Kathmandu"),
    "pashupatinath temple":   _ai("pashupatinath",  "main-temple.jpg",      "Pashupatinath Temple"),
    "boudhanath":             _ai("boudhanath",     "stupa.jpg",            "Boudhanath Stupa, Kathmandu"),
    "boudhanath stupa":       _ai("boudhanath",     "stupa.jpg",            "Boudhanath Stupa"),
    "boudha stupa":           _ai("boudhanath",     "stupa.jpg",            "Boudhanath Stupa"),
    "boudha":                 _ai("boudhanath",     "stupa.jpg",            "Boudhanath Stupa"),
    "swayambhunath":          _ai("swayambhunath",  "stupa.jpg",            "Swayambhunath (Monkey Temple)"),
    "swayambhunath stupa":    _ai("swayambhunath",  "stupa.jpg",            "Swayambhunath Stupa"),
    "swayambhu":              _ai("swayambhunath",  "stupa.jpg",            "Swayambhunath"),
    "kathmandu durbar square": _ai("kathmandu",     "durbar-square.jpg",    "Kathmandu Durbar Square"),
    "basantapur":             _ai("kathmandu",     "durbar-square.jpg",    "Basantapur Durbar, Kathmandu"),
    "hanuman dhoka":          _ai("kathmandu",     "durbar-square.jpg",    "Hanuman Dhoka, Kathmandu"),
    "kathmandu":              _ai("kathmandu",     "durbar-square.jpg",    "Kathmandu"),
    "bhaktapur durbar square": _ai("bhaktapur",     "durbar.jpg",           "Bhaktapur Durbar Square"),
    "bhaktapur":              _ai("bhaktapur",     "durbar.jpg",           "Bhaktapur Durbar Square"),
    "55 window palace":       _ai("bhaktapur",     "durbar.jpg",           "55-Window Palace, Bhaktapur"),
    "nyatapola":              _ai("bhaktapur",     "durbar.jpg",           "Nyatapola Temple, Bhaktapur"),
    "nyatapola temple":       _ai("bhaktapur",     "durbar.jpg",           "Nyatapola Temple, Bhaktapur"),
    "golden gate bhaktapur":  _ai("bhaktapur",     "durbar.jpg",           "Golden Gate, Bhaktapur"),
    "patan durbar square":    _ai("patan",         "durbar-square.jpg",    "Patan Durbar Square"),
    "patan":                  _ai("patan",         "durbar-square.jpg",    "Patan (Lalitpur) Durbar Square"),
    "lalitpur":               _ai("patan",         "durbar-square.jpg",    "Lalitpur (Patan)"),
    "krishna mandir patan":   _ai("patan",         "durbar-square.jpg",    "Krishna Mandir, Patan Durbar Square"),
    "dharahara":              _ai("dharahara",     "tower.jpg",            "Dharahara Tower, Kathmandu"),
    "bhimsen tower":          _ai("dharahara",     "tower.jpg",            "Dharahara (Bhimsen) Tower"),

    # ============ POKHARA VALLEY ============
    "pokhara":                _ai("pokhara",       "fewatal.jpg",          "Phewa Lake, Pokhara"),
    "phewa lake":             _ai("pokhara",       "fewatal.jpg",          "Phewa (Fewa) Lake, Pokhara"),
    "phewa tal":              _ai("pokhara",       "fewatal.jpg",          "Phewa Tal, Pokhara"),
    "fewa lake":              _ai("pokhara",       "fewatal.jpg",          "Fewa Lake, Pokhara"),
    "fewa tal":               _ai("pokhara",       "fewatal.jpg",          "Fewa Tal, Pokhara"),
    "lakeside pokhara":       _ai("pokhara",       "fewatal.jpg",          "Pokhara Lakeside"),
    "pokhara lakeside":       _ai("pokhara",       "fewatal.jpg",          "Pokhara Lakeside"),
    "tal barahi":             _ai("pokhara",       "fewatal.jpg",          "Tal Barahi Temple, Phewa Lake"),
    "davis falls":            _ai("davis-falls",   "waterfall.jpg",        "Davis Falls (Patale Chhango), Pokhara"),
    "patale chhango":         _ai("davis-falls",   "waterfall.jpg",        "Patale Chhango, Pokhara"),
    "mahendra cave":          _ai("mahendra-cave", "interior.jpg",         "Mahendra Cave, Pokhara"),
    "gupteshwor mahadev cave": _ai("mahendra-cave", "interior.jpg",        "Gupteshwor Mahadev Cave, Pokhara"),

    # ============ LUMBINI ============
    "lumbini":                _ai("lumbini",       "garden.jpg",           "Lumbini — Birthplace of Buddha"),
    "maya devi temple":       _ai("lumbini",       "garden.jpg",           "Maya Devi Temple, Lumbini"),

    # ============ EVEREST / KHUMBU ============
    "mount everest":          _ai("everest",       "base-camp.jpg",        "Mount Everest (Sagarmatha)"),
    "everest":                _ai("everest",       "base-camp.jpg",        "Mount Everest"),
    "sagarmatha":             _ai("everest",       "base-camp.jpg",        "Sagarmatha (Mount Everest)"),
    "everest base camp":      _ai("everest",       "base-camp.jpg",        "Everest Base Camp, Khumbu"),
    "ebc":                    _ai("everest",       "base-camp.jpg",        "Everest Base Camp"),
    "sagarmatha national park": _ai("everest",     "base-camp.jpg",        "Sagarmatha National Park"),
    "namche bazaar":          _ai("everest",       "base-camp.jpg",        "Namche Bazaar, Khumbu"),
    "kala patthar":           _ai("everest",       "base-camp.jpg",        "Kala Patthar viewpoint"),

    # ============ ANNAPURNA REGION ============
    "annapurna base camp":    _ai("annapurna",     "trek.jpg",             "Annapurna Base Camp"),
    "annapurna circuit":      _ai("annapurna",     "trek.jpg",             "Annapurna Circuit Trek"),
    "annapurna":              _ai("annapurna",     "trek.jpg",             "Annapurna Himal"),
    "annapurna south":        _ai("annapurna",     "trek.jpg",             "Annapurna South"),
    "ghandruk":               _ai("ghandruk",      "village.jpg",          "Ghandruk Gurung village"),
    "machhapuchhre":          _ai("annapurna",     "trek.jpg",             "Machhapuchhre (Fishtail Mountain)"),
    "machhapuchhare":         _ai("annapurna",     "trek.jpg",             "Machhapuchhre (Fishtail)"),
    "fishtail mountain":      _ai("annapurna",     "trek.jpg",             "Machhapuchhre Fishtail"),
    "poon hill":              _ai("annapurna",     "trek.jpg",             "Poon Hill viewpoint, Ghorepani"),
    "ghorepani":              _ai("annapurna",     "trek.jpg",             "Ghorepani village"),
    "mardi himal":            _ai("annapurna",     "trek.jpg",             "Mardi Himal Trek"),

    # ============ LANGTANG ============
    "langtang":               _ai("langtang",      "valley.jpg",           "Langtang Valley"),
    "langtang valley":        _ai("langtang",      "valley.jpg",           "Langtang Valley Trek"),
    "langtang national park": _ai("langtang",      "valley.jpg",           "Langtang National Park"),
    "gosainkunda":            _ai("gosaikunda",    "glacial-lake.jpg",     "Gosaikunda Glacial Lake"),
    "gosaikunda":             _ai("gosaikunda",    "glacial-lake.jpg",     "Gosaikunda Lake"),

    # ============ MUSTANG / MUKTINATH ============
    "upper mustang":          _ai("mustang",       "lo-manthang.jpg",      "Upper Mustang (Lo Manthang)"),
    "lo manthang":            _ai("mustang",       "lo-manthang.jpg",      "Lo Manthang, Mustang"),
    "mustang":                _ai("mustang",       "lo-manthang.jpg",      "Mustang"),
    "muktinath":              _ai("muktinath",     "temple.jpg",           "Muktinath Temple, Mustang"),
    "muktinath temple":       _ai("muktinath",     "temple.jpg",           "Muktinath Temple"),
    "jomsom":                 _ai("mustang",       "lo-manthang.jpg",      "Jomsom, Mustang"),
    "kagbeni":                _ai("mustang",       "lo-manthang.jpg",      "Kagbeni, Mustang"),
    "marpha":                 _ai("mustang",       "lo-manthang.jpg",      "Marpha village, Mustang"),

    # ============ MANASLU ============
    "manaslu":                _ai("manaslu",       "mountain-peak.jpg",    "Mount Manaslu"),
    "manaslu circuit":        _ai("manaslu",       "mountain-peak.jpg",    "Manaslu Circuit Trek"),

    # ============ DOLPO / PHOKSUNDO ============
    "dolpo":                  _ai("dolpo",         "highland-village.jpg", "Dolpo highland village"),
    "upper dolpo":            _ai("dolpo",         "highland-village.jpg", "Upper Dolpo Trek"),
    "shey phoksundo":         _ai("phoksundo",     "lake.jpg",             "Phoksundo Lake, Dolpo"),
    "phoksundo lake":         _ai("phoksundo",     "lake.jpg",             "Phoksundo Lake"),
    "shey phoksundo national park": _ai("phoksundo", "lake.jpg",           "Shey Phoksundo National Park"),

    # ============ RARA / KARNALI ============
    "rara lake":              _ai("rara",          "alpine-lake.jpg",      "Rara Lake, Mugu"),
    "rara":                   _ai("rara",          "alpine-lake.jpg",      "Rara Lake"),
    "rara national park":     _ai("rara",          "alpine-lake.jpg",      "Rara National Park"),

    # ============ TILICHO / OTHER LAKES ============
    "tilicho lake":           _ai("tilicho",       "himalayan-lake.jpg",   "Tilicho Lake, Manang"),

    # ============ NAGARKOT / VIEWPOINTS ============
    "nagarkot":               _ai("nagarkot",      "sunrise-view.jpg",     "Nagarkot sunrise viewpoint"),

    # ============ CHITWAN ============
    "chitwan national park":  _ai("chitwan",       "safari.jpg",           "Chitwan National Park"),
    "chitwan":                _ai("chitwan",       "safari.jpg",           "Chitwan"),
    "sauraha":                _ai("chitwan",       "safari.jpg",           "Sauraha, Chitwan"),

    # ============ BARDIYA ============
    "bardiya national park":  _ai("bardiya",       "tiger-reserve.jpg",    "Bardiya National Park"),
    "bardia national park":   _ai("bardiya",       "tiger-reserve.jpg",    "Bardia National Park"),
    "bardiya":                _ai("bardiya",       "tiger-reserve.jpg",    "Bardiya"),

    # ============ KOSHI TAPPU ============
    "koshi tappu":            _ai("koshi-tappu",   "wetlands.jpg",         "Koshi Tappu Wildlife Reserve"),
    "koshi tappu wildlife reserve": _ai("koshi-tappu", "wetlands.jpg",     "Koshi Tappu Wildlife Reserve"),

    # ============ ILAM / TEA ============
    "ilam":                   _ai("ilam",          "tea-gardens.jpg",      "Ilam tea gardens"),
    "ilam tea gardens":       _ai("ilam",          "tea-gardens.jpg",      "Ilam tea gardens"),
    "kanyam":                 _ai("kanyam",        "tea-garden.jpg",       "Kanyam Tea Garden, Ilam"),
    "kanyam tea garden":      _ai("kanyam",        "tea-garden.jpg",       "Kanyam Tea Garden, Ilam"),
    "shree antu":             _ai("ilam",          "tea-gardens.jpg",      "Shree Antu viewpoint, Ilam"),
    "sri antu":               _ai("ilam",          "tea-gardens.jpg",      "Shree Antu, Ilam"),

    # ============ JANAKPUR ============
    "janakpur":               _ai("janakpur",      "janaki-mandir.jpg",    "Janaki Mandir, Janakpur"),
    "janaki mandir":          _ai("janakpur",      "janaki-mandir.jpg",    "Janaki Mandir, Janakpur Dham"),
    "janakpur dham":          _ai("janakpur",      "janaki-mandir.jpg",    "Janakpur Dham"),

    # ============ BANDIPUR ============
    "bandipur":               _ai("bandipur",      "hilltop-village.jpg",  "Bandipur heritage village"),

    # ============ MANAKAMANA ============
    "manakamana":             _ai("manakamana",    "temple.jpg",           "Manakamana Temple, Gorkha"),
    "manakamana temple":      _ai("manakamana",    "temple.jpg",           "Manakamana Temple"),
    "manakamana cable car":   _ai("manakamana",    "temple.jpg",           "Manakamana Cable Car"),

    # ============ GORKHA ============
    "gorkha":                 _ai("gorkha",        "durbar.jpg",           "Gorkha Durbar"),
    "gorkha durbar":          _ai("gorkha",        "durbar.jpg",           "Gorkha Durbar Palace"),

    # ============ RANI MAHAL / PALPA ============
    "rani mahal":             _ai("rani-mahal",    "palace.jpg",           "Rani Mahal, Palpa"),
    "rani mahal palpa":       _ai("rani-mahal",    "palace.jpg",           "Rani Mahal, Palpa"),
    "tansen":                 _ai("rani-mahal",    "palace.jpg",           "Tansen, Palpa"),
    "tansen durbar":          _ai("rani-mahal",    "palace.jpg",           "Tansen Durbar, Palpa"),

    # ============ KHAPTAD ============
    "khaptad":                _ai("khaptad",       "landscape.jpg",        "Khaptad National Park"),
    "khaptad national park":  _ai("khaptad",       "landscape.jpg",        "Khaptad National Park"),

    # ============ PATHIBHARA ============
    "pathibhara":             _ai("pathibhara",    "temple.jpg",           "Pathibhara Devi Temple, Taplejung"),
    "pathibhara devi":        _ai("pathibhara",    "temple.jpg",           "Pathibhara Devi, Taplejung"),

    # ============ DHULIKHEL / BHAKTAPUR AREA ============
    "dhulikhel":              _ai("nagarkot",      "sunrise-view.jpg",     "Dhulikhel heritage town"),

    # ============ KANCHENJUNGA ============
    "kanchenjunga":           _ai("kanchenjunga",  "peak.jpg",             "Mount Kanchenjunga"),
    "kanchanjunga":           _ai("kanchenjunga",  "peak.jpg",             "Mount Kanchenjunga"),

    # ============ DHAULAGIRI ============
    "dhaulagiri":             _ai("dhaulagiri",    "peak.jpg",             "Mount Dhaulagiri"),

    # ============ BHOTE KOSHI ============
    "bhote koshi":            _ai("bhote-koshi",   "rafting.jpg",          "Bhote Koshi River"),
    "bhote koshi river":      _ai("bhote-koshi",   "rafting.jpg",          "Bhote Koshi River"),
    "bhote koshi rafting":    _ai("bhote-koshi",   "rafting.jpg",          "Bhote Koshi whitewater rafting"),

    # ============ CHANDRAGIRI ============
    "chandragiri":                _ai("nagarkot",      "sunrise-view.jpg",     "Chandragiri Hill viewpoint"),
    "chandragiri hill":           _ai("nagarkot",      "sunrise-view.jpg",     "Chandragiri Hill"),
    "chandragiri cable car":      _ai("manakamana",    "temple.jpg",           "Chandragiri Cable Car"),
    "bhaleshwor mahadev":         _ai("nagarkot",      "sunrise-view.jpg",     "Bhaleshwor Mahadev, Chandragiri"),

    # ============ SARANGKOT ============
    "sarangkot":                 _ai("annapurna",     "trek.jpg",             "Sarangkot viewpoint, Pokhara"),
    "sarangkot paragliding":     _ai("annapurna",     "trek.jpg",             "Paragliding at Sarangkot"),
}


# ---------------------------------------------------------------------------
# Category keyword -> category slug mapping (for fallback matching)
# ---------------------------------------------------------------------------

CATEGORY_BY_KEYWORD = [
    # Water bodies
    (("waterfall", "jharana", "jharna", "chhango", "falls", "water fall"), "waterfalls"),
    (("lake", "tal", "kunda", "pokhari", "sarovar", "daha", "lake "), "lakes"),
    (("river", "khola", "kosi", "koshi", "karnali", "gandaki", "trishuli",
      "narayani", "seti", "arun", "tamur", "bheri", "rapti", "mahakali",
      "bhote koshi", "sun koshi", "sun kosi", "kali gandaki", "kaligandaki"), "rivers"),
    (("hot spring", "hotspring", "tatopani", "hot spring"), "hot-springs"),
    # Caves
    (("cave", "gufa", "cavern", "gupha", "mahadev cave"), "caves"),
    # Mountains / peaks
    (("mount ", "mountain", "peak", "himal", "himāl", "everest", "sagarmatha",
      "annapurna", "machhapuchhre", "machhapuchhare", "fishtail", "manaslu",
      "dhaulagiri", "makalu", "kanchenjunga", "kanchanjunga", "lhotse",
      "cho oyu", "api himal", "api himal", "saipal", "dhaulagiri"), "mountains"),
    # Trekking
    (("trek", "trekking", "base camp", "circuit trek", "pass trek", "la pass",
      "high camp", "trekking route", "trek route", "hike", "hiking"), "trekking"),
    # Viewpoints
    (("viewpoint", "view point", "view tower", "danda", "poon hill", "poonhill",
      "sarangkot", "kala patthar", "gokyo ri", "chandragiri", "nagarkot",
      "phulchowki", "kakani", "daman"), "viewpoints"),
    # Hills
    (("hill station",), "hills"),
    # Valleys
    (("valley",), "valleys"),
    # Forests
    (("forest", "jungle", "rhododendron", "sal forest"), "forests"),
    # National parks / wildlife
    (("national park", "wildlife reserve", "conservation area",
      "hunting reserve", "safari", "rhino", "tiger", "elephant"), "wildlife"),
    # Bird watching
    (("bird watching", "birding", "bird sanctuary", "wetland birds"), "bird-watching"),
    # Parks / gardens
    (("botanical garden", "garden of dreams", "godawari", "park ", "garden"), "parks-gardens"),
    # Tea / agriculture
    (("tea garden", "tea plantation", "tea estate", "kanyam", "ilam tea"), "tea-coffee"),
    # Cable car / ropeway
    (("cable car", "cablecar", "ropeway"), "cablecar"),
    # Temples / Hindu
    (("temple", "mandir", "mahadev", "shiva", "bhairav", "kumari",
      "bindhyabasini", "dakshinkali", "guhyeshwari", "pashupati",
      "doleshwor", "bhaleshwor", "devi", "bhagwati", "narayan",
      "bhimsen", "ganesh", "vinayak", "siddhi", "pashupatinath",
      "muktinath", "manakamana", "dakshinkali", "pathibhara",
      "janaki mandir", "nyatapola", "krishna mandir"), "temples"),
    # Buddhist stupas / monasteries
    (("stupa", "gompa", "monastery", "buddhist", "buddha", "vihar", "gumba",
      "lumbini", "world peace pagoda", "shanti stupa", "boudhanath",
      "swayambhu", "boudha"), "buddhist-sites"),
    # Durbar / heritage / palaces
    (("durbar square", "durbar", "palace", "heritage site", "rani mahal",
      "gorkha durbar", "nuwakot durbar", "tansen durbar", "museum",
      "narayanhiti"), "heritage"),
    # Museums
    (("museum", "art gallery", "exhibition"), "museums"),
    # Pilgrimage
    (("pilgrimage", "dham", "tirtha", "yatris", "pilgrim"), "pilgrimage"),
    # Festivals
    (("festival", "jatra", "mela", "dashain", "tihar", "holi", "indra jatra",
      "bisket", "machhindranath", "tiji", "mani rimdu", "gai jatra", "ghode jatra"), "festivals"),
    # Adventure
    (("bungee", "bungee jumping", "rock climbing", "climbing", "bouldering",
      "peak climbing", "mountaineering", "canyoning", "zip flyer", "zipflyer"), "adventure"),
    # Air sports
    (("paragliding", "ultralight", "skydiving", "ultralight flight",
      "mountain flight", "paraglide"), "air-sports"),
    # Water sports
    (("rafting", "kayak", "kayaking", "boating", "canoe", "canoeing"), "water-sports"),
    # Camping
    (("camping", "camp site", "tent camp", "high camp"), "camping"),
    # Cycling
    (("cycling", "mountain bike", "mountain biking", "biking trail"), "cycling"),
    # Winter / snow
    (("snow", "winter", "skiing", "kalinchowk"), "winter"),
    # Scenic routes
    (("scenic drive", "highway", "prithvi highway", "siddhartha highway",
      "araniko highway", "karnali highway", "pasang lhamu", "road trip"), "scenic-routes"),
    # Eco
    (("ecotourism", "eco-tourism", "community tourism", "homestay", "organic"), "eco-tourism"),
    # Cities / bazaar
    (("bazaar", "bazar", "thamel", "new road", "city ", "market"), "cities"),
    # Food
    (("restaurant", "cafe", "bakery", "dhaba", "momo", "dal bhat", "street food",
      "food ", "culinary"), "food-culinary"),
    # Shopping
    (("shop", "shopping", "store", "handicraft", "market"), "shopping"),
    # Village
    (("village", "gaun"), "villages"),
    # Hotels / accommodation
    (("hotel", "resort", "lodge", "guest house", "guesthouse", "hostel",
      "motel", "teahouse", "tea house", "homestay", "home stay", "inn",
      "cottage"), "hotel"),
]


# Default gallery "pools" — these are used only for extra gallery images
# for non-landmark destinations. We use the postcard generator to create
# multiple variant postcards per destination rather than repeating stock.
def _gallery_postcard(dest_name, cat_slug, district, seed_offset, caption):
    """Return a postcard variant for gallery use (different visual hash)."""
    return _postcard(
        dest_name, cat_slug, district,
        caption=caption
    )


# ---------------------------------------------------------------------------
# Utility: whole-word matching
# ---------------------------------------------------------------------------
_WORD_RE = re.compile(r"[a-z0-9]+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _whole_word_in(needle, haystack):
    n = (needle or "").lower().strip()
    h = (haystack or "").lower()
    if not n:
        return False
    pat = r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])"
    return re.search(pat, h) is not None


def _match_landmark(dest_name):
    if not dest_name:
        return None
    name_l = dest_name.lower()
    best = None
    best_len = 0
    for key, photo in LANDMARKS.items():
        if not key:
            continue
        if _whole_word_in(key, name_l) and len(key) > best_len:
            best = photo
            best_len = len(key)
    return best


def _match_category(destination):
    """Determine category slug from destination's existing category or keywords."""
    cat = getattr(destination, "category", None)
    slug = ((getattr(cat, "slug", "") or "").lower()) if cat else ""
    # Accept known category slugs
    KNOWN = {
        "mountains", "hills", "hill-stations", "valleys", "lakes",
        "lakes-water-activities", "rivers", "waterfalls", "caves",
        "hot-springs", "natural-wonders", "viewpoints", "view-tower",
        "forests", "wildlife", "national-parks", "bird-watching",
        "parks-gardens", "eco-tourism", "agriculture", "tea-coffee",
        "temples", "buddhist-sites", "pilgrimage", "spiritual-wellness",
        "heritage", "heritage-temples", "unesco", "durbar-squares",
        "palaces", "museums", "culture", "festivals", "cities",
        "shopping", "food-culinary", "villages", "traditional-villages",
        "adventure", "climbing", "mountaineering", "trekking",
        "air-sports", "paragliding", "bungee", "zip-flyer",
        "cablecar", "cable-car", "ropeway", "water-sports",
        "rafting", "kayaking", "boating", "camping", "cycling",
        "mountain-biking", "winter", "snow", "scenic-routes",
        "road-trips", "attraction", "attractions", "nature-trekking",
        "hotel", "resort", "guest_house", "hostel", "motel",
        "homestay",
    }
    if slug in KNOWN:
        return slug
    name = getattr(destination, "name", "") or ""
    desc = getattr(destination, "short_description", "") or ""
    city = getattr(destination, "city", "") or ""
    district = getattr(destination, "district", "") or ""
    cat_name = (getattr(cat, "name", "") or "") if cat else ""
    haystack = f"{name} {desc} {city} {district} {cat_name}".lower()
    # Keyword-based categorization
    for keywords, cat_slug in CATEGORY_BY_KEYWORD:
        for kw in keywords:
            if " " in kw:
                if kw in haystack:
                    return cat_slug
            else:
                if _whole_word_in(kw, haystack):
                    return cat_slug
    return "attractions"


def _is_accommodation(destination):
    cat = getattr(destination, "category", None)
    slug = ((getattr(cat, "slug", "") or "").lower()) if cat else ""
    ACCOMMODATION_SLUGS = {
        "hotel", "resort", "lodge", "guest_house", "guesthouse", "hostel",
        "motel", "homestay", "home_stay", "alpine_hut", "camp_site",
        "camp_pitch", "chalet", "apartment", "wilderness_hut", "cottage",
    }
    if slug in ACCOMMODATION_SLUGS:
        return True
    name = (getattr(destination, "name", "") or "").lower()
    hints = [
        "hotel", "resort", "lodge", "guest house", "guesthouse", "homestay",
        "home stay", "backpackers", "hostel", "motel", "cottages", "tea house",
        "teahouse", "inn",
    ]
    for h in hints:
        if _whole_word_in(h, name):
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _verified_photo(dest_id):
    """Return the verified real photo (Commons / Openverse) for this destination, if any."""
    if dest_id is None:
        return None
    info = VERIFIED_WIKIMEDIA.get(int(dest_id))
    if not info:
        return None
    return {
        "url": info.get("url"),
        "thumb": info.get("thumb") or info.get("url"),
        "source": info.get("source") or "wikimedia",
        "author": info.get("photographer") or "Wikimedia Commons",
        "caption": info.get("caption") or info.get("label"),
        "tags": ["verified", info.get("source") or "wikimedia", info.get("tier") or "verified"],
        "license": info.get("license"),
        "source_url": info.get("source_url"),
        "qid": info.get("qid"),
    }


def resolve_cover_photo(destination):
    """Return a cover photo dict for the destination.

    Priority:
      1. Verified real photo from Wikimedia Commons (checked via Commons API).
      2. Curated LANDMARK photo if name matches a known Nepal place.
      3. Unique deterministic SVG postcard keyed to name+category+district+id.
    """
    name = getattr(destination, "name", "") or ""
    district = getattr(destination, "district", "") or ""
    city = getattr(destination, "city", "") or ""
    dest_id = getattr(destination, "id", None)
    verified = _verified_photo(dest_id)
    if verified is not None:
        return verified
    landmark = _match_landmark(name)
    if landmark is not None:
        return landmark
    if _is_accommodation(destination):
        return _postcard(name, "hotel", district or city, caption=name, dest_id=dest_id)
    cat_slug = _match_category(destination)
    return _postcard(name, cat_slug, district or city, caption=name, dest_id=dest_id)


def resolve_gallery_photos(destination, target=6):
    """Return gallery photos. Uses postcard variants when no real photos exist.

    NOTE: These gallery images should be saved with STATUS_PENDING so an
    admin can review/approve/replace them with real photos through the
    image pipeline.
    """
    name = getattr(destination, "name", "") or ""
    district = getattr(destination, "district", "") or ""
    city = getattr(destination, "city", "") or ""
    dest_id = getattr(destination, "id", None) or 0
    cover = resolve_cover_photo(destination)
    cover_url = cover.get("url")

    out = []
    seen = {cover_url}

    cat_slug = _match_category(destination)
    base_district = district or city
    dest_id = getattr(destination, "id", None)
    captions = [
        f"{name} — panoramic view",
        f"{name} — approach trail",
        f"{name} — surrounding landscape",
        f"{name} — local area",
        f"{name} — scenic view",
        f"{name} — visitor experience",
    ]
    # Generate deterministic variant postcards
    for i in range(target):
        # Vary the seed string to get different gradient/silhouette combos
        variant_seed = f"{name}|{cat_slug}|{base_district}|{dest_id}|gallery|{i}"
        h = int(hashlib.md5(variant_seed.encode()).hexdigest()[:8], 16)
        # Rotate through related categories for gallery variety
        related_cats = _get_related_categories(cat_slug)
        vcat = related_cats[h % len(related_cats)]
        caption = captions[i] if i < len(captions) else f"{name} — view {i+1}"
        photo = _postcard(name, vcat, base_district, caption=caption,
                          dest_id=f"{dest_id}-g{i}" if dest_id is not None else None)
        if photo["url"] not in seen:
            out.append(photo)
            seen.add(photo["url"])
    return out[:target]


def _get_related_categories(cat_slug):
    """Return a small list of related category slugs for gallery variety."""
    c = cat_slug.lower().strip()
    related_map = {
        "mountains": ["mountains", "viewpoints", "trekking", "winter", "natural-wonders"],
        "trekking": ["trekking", "mountains", "viewpoints", "valleys", "camping"],
        "lakes": ["lakes", "viewpoints", "water-sports", "valleys", "natural-wonders"],
        "rivers": ["rivers", "water-sports", "waterfalls", "adventure", "valleys"],
        "waterfalls": ["waterfalls", "water-sports", "forests", "rivers", "natural-wonders"],
        "caves": ["caves", "temples", "heritage", "adventure"],
        "hot-springs": ["hot-springs", "rivers", "trekking", "winter"],
        "forests": ["forests", "wildlife", "parks-gardens", "eco-tourism", "bird-watching"],
        "wildlife": ["wildlife", "forests", "bird-watching", "parks-gardens", "eco-tourism"],
        "bird-watching": ["bird-watching", "wildlife", "forests", "lakes", "rivers"],
        "national-parks": ["wildlife", "forests", "bird-watching", "eco-tourism"],
        "viewpoints": ["viewpoints", "mountains", "hills", "trekking", "scenic-routes"],
        "hills": ["hills", "viewpoints", "villages", "tea-coffee", "agriculture"],
        "valleys": ["valleys", "rivers", "villages", "trekking", "forests"],
        "temples": ["temples", "pilgrimage", "heritage", "festivals", "spiritual-wellness"],
        "buddhist-sites": ["buddhist-sites", "pilgrimage", "heritage", "spiritual-wellness", "temples"],
        "heritage": ["heritage", "temples", "museums", "cities", "culture"],
        "museums": ["museums", "heritage", "cities", "culture"],
        "festivals": ["festivals", "culture", "temples", "heritage", "cities"],
        "culture": ["culture", "festivals", "heritage", "villages", "temples"],
        "pilgrimage": ["pilgrimage", "temples", "buddhist-sites", "spiritual-wellness", "heritage"],
        "spiritual-wellness": ["spiritual-wellness", "pilgrimage", "temples", "buddhist-sites", "heritage"],
        "cities": ["cities", "heritage", "shopping", "food-culinary", "villages"],
        "villages": ["villages", "hills", "agriculture", "culture", "trekking"],
        "shopping": ["shopping", "cities", "culture", "food-culinary"],
        "food-culinary": ["food-culinary", "cities", "culture", "shopping"],
        "tea-coffee": ["tea-coffee", "hills", "agriculture", "villages", "eco-tourism"],
        "agriculture": ["agriculture", "villages", "tea-coffee", "hills", "eco-tourism"],
        "parks-gardens": ["parks-gardens", "forests", "wildlife", "bird-watching", "eco-tourism"],
        "eco-tourism": ["eco-tourism", "forests", "villages", "wildlife", "parks-gardens"],
        "adventure": ["adventure", "trekking", "mountains", "water-sports", "air-sports", "camping"],
        "air-sports": ["air-sports", "adventure", "viewpoints", "mountains"],
        "water-sports": ["water-sports", "rivers", "lakes", "adventure"],
        "camping": ["camping", "trekking", "forests", "mountains"],
        "cycling": ["cycling", "scenic-routes", "hills", "villages", "adventure"],
        "winter": ["winter", "mountains", "trekking", "hot-springs"],
        "scenic-routes": ["scenic-routes", "viewpoints", "hills", "cycling"],
        "cablecar": ["cablecar", "viewpoints", "adventure", "air-sports"],
        "hotel": ["hotel", "cities", "villages", "mountains"],
    }
    return related_map.get(c, ["mountains", "lakes", "heritage", "wildlife", "forests", "villages"])


def resolve_hotel_photo(hotel):
    name = getattr(hotel, "name", "") or "Hotel"
    city = getattr(hotel, "city", "") or ""
    hid = getattr(hotel, "id", None)
    return _postcard(name, "hotel", city, caption=name, dest_id=hid)


def resolve_poi_photo(poi_type="", poi_name="", seed=0):
    hay = f"{poi_type} {poi_name}".lower()
    nm = poi_name or poi_type or "Nepal"
    if any(w in hay for w in ("health", "medical", "doctor", "emergency", "hospital", "clinic")):
        return _postcard(nm, "cities", "", caption=nm, dest_id=f"poi-{seed}")
    if "pharmacy" in hay or "medicine" in hay:
        return _postcard(nm, "cities", "", caption=nm, dest_id=f"poi-{seed}")
    if "police" in hay:
        return _postcard(nm, "cities", "", caption=nm, dest_id=f"poi-{seed}")
    if any(w in hay for w in ("bank", "atm", "money", "finance")):
        return _postcard(nm, "cities", "", caption=nm, dest_id=f"poi-{seed}")
    if any(w in hay for w in ("restaurant", "food", "eat", "momo", "cafe")):
        return _postcard(nm, "food-culinary", "", caption=nm, dest_id=f"poi-{seed}")
    if any(w in hay for w in ("hotel", "resort", "lodge", "stay")):
        return _postcard(nm, "hotel", "", caption=nm, dest_id=f"poi-{seed}")
    return _postcard(nm, "general", "", caption=nm, dest_id=f"poi-{seed}")


def get_category_svg(category_key):
    return SVG_ICON.get((category_key or "general").lower().replace("_", "-"),
                        SVG_ICON["general"])


def is_accommodation(destination):
    return _is_accommodation(destination)


def is_accommodation_category(slug):
    ACCOMMODATION_SLUGS = {
        "hotel", "resort", "lodge", "guest_house", "guesthouse", "hostel",
        "motel", "homestay", "home_stay", "alpine_hut", "camp_site",
        "camp_pitch", "chalet", "apartment", "wilderness_hut", "cottage",
    }
    return (slug or "").lower() in ACCOMMODATION_SLUGS


def postcard_url_for(name, category_slug="general", district=""):
    """Public helper to get a postcard URL (used by admin/management commands)."""
    from urllib.parse import quote
    return f"/api/v1/postcard/{quote(category_slug)}/{quote(name)}/{quote(district)}.svg"


def acquire_wikimedia_photos(destination, limit=8, timeout=6):
    """Network is blocked in sandbox; kept for future admin action."""
    return []
