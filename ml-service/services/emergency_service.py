"""
services/emergency_service.py

Serves the emergency directory. Each category lives in its own file under
data/emergency/ (hotlines.json, hospitals.json, pharmacies.json,
banks.json, police_stations.json, embassies.json, local_government.json,
hotels.json, languages.json) so nothing gets mixed together - add a new
entry to the right file and it shows up automatically, no code change
needed.
"""
import json
import os
from math import radians, sin, cos, sqrt, atan2

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "emergency")

# category name -> filename (also doubles as the list of valid ?category=
# values for the /emergency/nearest endpoint)
FACILITY_FILES = {
    "hospital": "hospitals.json",
    "pharmacy": "pharmacies.json",
    "bank": "banks.json",
    "police_station": "police_stations.json",
    "embassy": "embassies.json",
    "local_government": "local_government.json",
    "hotel": "hotels.json",
}

_cache: dict = {}


def _load(filename: str) -> list:
    if filename not in _cache:
        path = os.path.join(DATA_DIR, filename)
        with open(path, encoding="utf-8") as f:
            _cache[filename] = json.load(f)
    return _cache[filename]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def get_national_hotlines() -> list:
    return _load("hotlines.json")


def get_languages() -> list:
    return _load("languages.json")


def get_facilities(category: str) -> list:
    """Every entry in a category file, e.g. get_facilities('hospital')."""
    filename = FACILITY_FILES.get(category)
    if not filename:
        return []
    return _load(filename)


def get_region(city: str) -> dict:
    """All categories for one city, assembled on the fly from the
    per-category files (so there's still a single call for 'give me
    everything about Pokhara')."""
    result = {"city": city, "facilities": {}}
    for category, filename in FACILITY_FILES.items():
        matches = [f for f in _load(filename) if f["region"].lower() == city.lower()]
        if matches:
            result["facilities"][category] = matches
    return result


def nearest_facilities(lat: float, lon: float, category: str | None = None, limit: int = 5) -> list:
    """Find nearest facilities to a GPS point. Pass category to restrict
    to one file (hospital, pharmacy, bank, police_station, embassy,
    local_government, hotel); omit it to search across all of them."""
    categories = [category] if category else list(FACILITY_FILES.keys())
    results = []
    for cat in categories:
        for facility in get_facilities(cat):
            dist = haversine_km(lat, lon, facility["lat"], facility["lon"])
            results.append({**facility, "category": cat, "distance_km": round(dist, 1)})

    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]