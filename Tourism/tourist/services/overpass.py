"""
tourist/services/overpass.py

A real Overpass API (OpenStreetMap) service layer: two categorized query
sets — essential services (hospital/clinic/pharmacy/police/etc, with phone
numbers where OSM has them) and tourism places (attractions, viewpoints,
museums, hotels, restaurants, cafes, monuments, natural features, hiking
routes) — plus sync functions that persist results into Django
(OSMEssentialService / OSMTourismPlace, see models.py).

Free, no API key required. Uses the public Overpass instance by default
(OVERPASS_API_URL in settings), configurable for a self-hosted instance if
you outgrow the public rate limits.

Usage:
    from tourist.services.overpass import sync_essential_services, sync_tourism_places

    sync_essential_services(latitude=28.2096, longitude=83.9856, radius_m=5000)
    sync_tourism_places(latitude=28.2096, longitude=83.9856, radius_m=5000)
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tag maps: {internal category value} -> [(osm_key, osm_value), ...]
# A category can match more than one OSM tag (e.g. "ambulance" is tagged a
# couple of different ways in practice).
# ---------------------------------------------------------------------------
ESSENTIAL_SERVICE_TAGS = {
    "hospital": [("amenity", "hospital")],
    "clinic": [("amenity", "clinic"), ("amenity", "doctors")],
    "pharmacy": [("amenity", "pharmacy")],
    "police": [("amenity", "police")],
    "armed_force": [("landuse", "military"), ("military", "barracks"), ("military", "office")],
    "fire_station": [("amenity", "fire_station")],
    "bank": [("amenity", "bank")],
    "ambulance": [("emergency", "ambulance_station"), ("amenity", "ambulance_station")],
    "municipality_office": [("office", "government"), ("amenity", "townhall")],
    "tourism_office": [("tourism", "information")],
    # Note: OSM has no place-tag for a phone hotline — "national disaster
    # helpline" is a phone NUMBER, not a mappable location. The closest
    # location-based proxy is the municipality/ward office, which is why
    # it's included above; pair this with Django's own EmergencyContact
    # ward-office rows (see import_ward_contacts) for actual hotline numbers.
}

TOURISM_PLACE_TAGS = {
    "attraction": [("tourism", "attraction")],
    "viewpoint": [("tourism", "viewpoint")],
    "museum": [("tourism", "museum")],
    "hotel": [("tourism", "hotel")],
    "information": [("tourism", "information")],
    "restaurant": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "monument": [("historic", "monument")],
    "peak": [("natural", "peak")],
    "waterfall": [("natural", "waterfall")],
    "hiking_path": [("highway", "path")],
    "hiking_route": [("route", "hiking")],
}


# ---------------------------------------------------------------------------
# Public nearby-POI catalogue (master spec §4). One entry per admin-visible
# category: OSM tag pairs stay code-managed (admins configure labels, icons,
# ordering, limits and on/off — never raw Overpass strings, which would be an
# injection vector).
# ---------------------------------------------------------------------------
POI_CATEGORY_TAGS = {
    "hotels": [("tourism", "hotel"), ("tourism", "guest_house"), ("tourism", "hostel")],
    "hospitals": [("amenity", "hospital")],
    "clinics": [("amenity", "clinic"), ("amenity", "doctors")],
    "pharmacies": [("amenity", "pharmacy")],
    "temples": [("amenity", "place_of_worship")],  # religion kept per result
    "viewpoints": [("tourism", "viewpoint")],
    "attractions": [("tourism", "attraction")],
    "restaurants": [("amenity", "restaurant")],
    "cafes": [("amenity", "cafe")],
    "banks": [("amenity", "bank"), ("amenity", "bureau_de_change")],
    "atms": [("amenity", "atm")],
    "police": [("amenity", "police")],
    "fire_stations": [("amenity", "fire_station")],
    "bus_stations": [("amenity", "bus_station")],
    "airports": [("aeroway", "aerodrome")],
    "fuel": [("amenity", "fuel")],
    "supermarkets": [("shop", "supermarket"), ("shop", "mall")],
    "markets": [("amenity", "marketplace")],
    "museums": [("tourism", "museum")],
    "parks": [("leisure", "park")],
    "peaks": [("natural", "peak")],
    "waterfalls": [("waterway", "waterfall"), ("natural", "waterfall")],
    "lakes": [("natural", "water")],
    "trailheads": [("highway", "trailhead")],
    "parking": [("amenity", "parking")],
    "toilets": [("amenity", "toilets")],
    "embassies": [("amenity", "embassy")],
}

DEFAULT_POI_CATEGORIES = [
    {"key": "hotels", "label": "Hotels & lodges", "icon": "🏨", "enabled": True, "order": 1, "limit": 10},
    {"key": "hospitals", "label": "Hospitals", "icon": "🏥", "enabled": True, "order": 2, "limit": 10},
    {"key": "clinics", "label": "Clinics", "icon": "🩺", "enabled": True, "order": 3, "limit": 8},
    {"key": "pharmacies", "label": "Pharmacies", "icon": "💊", "enabled": True, "order": 4, "limit": 8},
    {"key": "temples", "label": "Temples & shrines", "icon": "🛕", "enabled": True, "order": 5, "limit": 10},
    {"key": "viewpoints", "label": "Viewpoints", "icon": "🔭", "enabled": True, "order": 6, "limit": 10},
    {"key": "attractions", "label": "Tourist attractions", "icon": "📍", "enabled": True, "order": 7, "limit": 10},
    {"key": "restaurants", "label": "Restaurants", "icon": "🍽️", "enabled": True, "order": 8, "limit": 10},
    {"key": "cafes", "label": "Cafés", "icon": "☕", "enabled": False, "order": 9, "limit": 8},
    {"key": "banks", "label": "Banks & exchange", "icon": "🏦", "enabled": True, "order": 10, "limit": 8},
    {"key": "atms", "label": "ATMs", "icon": "🏧", "enabled": False, "order": 11, "limit": 8},
    {"key": "police", "label": "Police", "icon": "🚓", "enabled": True, "order": 12, "limit": 5},
    {"key": "fire_stations", "label": "Fire stations", "icon": "🚒", "enabled": False, "order": 13, "limit": 5},
    {"key": "bus_stations", "label": "Bus stations", "icon": "🚌", "enabled": True, "order": 14, "limit": 5},
    {"key": "airports", "label": "Airports", "icon": "✈️", "enabled": False, "order": 15, "limit": 5},
    {"key": "fuel", "label": "Fuel stations", "icon": "⛽", "enabled": False, "order": 16, "limit": 8},
    {"key": "supermarkets", "label": "Supermarkets & malls", "icon": "🛒", "enabled": False, "order": 17, "limit": 8},
    {"key": "markets", "label": "Local markets", "icon": "🧺", "enabled": False, "order": 18, "limit": 8},
    {"key": "museums", "label": "Museums", "icon": "🏛️", "enabled": True, "order": 19, "limit": 8},
    {"key": "parks", "label": "Parks", "icon": "🌳", "enabled": False, "order": 20, "limit": 8},
    {"key": "peaks", "label": "Peaks & hills", "icon": "⛰️", "enabled": True, "order": 21, "limit": 10},
    {"key": "waterfalls", "label": "Waterfalls", "icon": "💧", "enabled": True, "order": 22, "limit": 8},
    {"key": "lakes", "label": "Lakes", "icon": "🌊", "enabled": False, "order": 23, "limit": 8},
    {"key": "trailheads", "label": "Trailheads", "icon": "🥾", "enabled": True, "order": 24, "limit": 8},
    {"key": "parking", "label": "Parking", "icon": "🅿️", "enabled": False, "order": 25, "limit": 8},
    {"key": "toilets", "label": "Public toilets", "icon": "🚻", "enabled": False, "order": 26, "limit": 8},
    {"key": "embassies", "label": "Embassies", "icon": "🏳️", "enabled": False, "order": 27, "limit": 5},
]


def get_poi_category_config():
    """Admin-editable POI category settings (SiteSetting key `poi_categories`).

    Admins may rename, re-order, enable/disable, and set per-category result
    limits. Overpass tag mappings stay code-managed for safety.
    """
    merged = {item["key"]: dict(item) for item in DEFAULT_POI_CATEGORIES}
    try:
        from tourist.models import SiteSetting
        setting = SiteSetting.objects.filter(key="poi_categories").first()
        stored = (setting.value if setting else None) or []
        if isinstance(stored, list):
            for row in stored:
                if not isinstance(row, dict):
                    continue
                key = str(row.get("key") or "")
                if key not in merged:
                    continue
                for field in ("label", "icon"):
                    if isinstance(row.get(field), str) and row[field].strip():
                        merged[key][field] = row[field].strip()[:60]
                if isinstance(row.get("enabled"), bool):
                    merged[key]["enabled"] = row["enabled"]
                if isinstance(row.get("order"), int):
                    merged[key]["order"] = row["order"]
                if isinstance(row.get("limit"), int) and 1 <= row["limit"] <= 25:
                    merged[key]["limit"] = row["limit"]
    except Exception:  # pragma: no cover - settings must never break search
        logger.warning("poi_categories setting unreadable; using defaults", exc_info=True)
    return sorted(merged.values(), key=lambda item: (item["order"], item["key"]))


def _poi_category_for_tags(tags):
    """Maps one OSM element's tags to a POI catalogue key (worship keeps religion in payload)."""
    if tags.get("amenity") == "place_of_worship":
        return "temples"
    for category, tag_pairs in POI_CATEGORY_TAGS.items():
        if category == "temples":
            continue
        for key, value in tag_pairs:
            if tags.get(key) == value:
                return category
    return None


def search_pois(latitude, longitude, radius_m, categories=None):
    """Coordinate-first nearby POI search (master spec §2).

    Returns (groups, categories_meta, error). `groups` maps category key ->
    list of place dicts sorted nearest-first; every place carries provenance
    (source, source_url, OSM id) plus phone/website/hours/address when OSM
    actually records them — never fabricated. On provider failure returns
    empty groups with `error` set so callers can still serve verified
    database places (fallback strategy, spec §60).
    """
    config = get_poi_category_config()
    enabled = [item for item in config if item["enabled"] and item["key"] in POI_CATEGORY_TAGS]
    if categories:
        wanted = set(categories)
        enabled = [item for item in enabled if item["key"] in wanted]
    groups = {item["key"]: [] for item in enabled}
    if not enabled:
        return groups, config, None
    clauses = []
    for item in enabled:
        for key, value in POI_CATEGORY_TAGS[item["key"]]:
            clauses.append(f'nwr["{key}"="{value}"](around:{int(radius_m)},{latitude},{longitude});')
    query = "[out:json][timeout:25];(\n" + "\n".join(clauses) + "\n);out center tags 400;"
    try:
        response = requests.post(settings.OVERPASS_API_URL, data={"data": query},
                                 headers={"User-Agent": "TourismApp/1.0", "Accept": "application/json"}, timeout=25)
        response.raise_for_status()
        elements = response.json().get("elements", [])
    except Exception as exc:  # any provider failure must degrade, never 500
        logger.warning("Overpass POI search failed: %s", exc)
        return groups, config, "Live map data (OpenStreetMap) is unavailable right now."
    limits = {item["key"]: item["limit"] for item in enabled}
    from tourist.utils import haversine_distance
    for element in elements:
        tags = element.get("tags") or {}
        key = _poi_category_for_tags(tags)
        if key not in groups:
            continue
        name = tags.get("name") or tags.get("name:en") or tags.get("operator")
        if not name:
            continue
        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        groups[key].append({
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "distance_km": round(haversine_distance(latitude, longitude, lat, lon), 2),
            "religion": tags.get("religion") if key == "temples" else None,
            "phone": tags.get("phone") or tags.get("contact:phone") or None,
            "website": tags.get("website") or tags.get("contact:website") or None,
            "opening_hours": tags.get("opening_hours") or None,
            "address": ", ".join(part for part in [tags.get("addr:street"), tags.get("addr:city")] if part) or None,
            "osm_id": element.get("id"),
            "osm_type": element.get("type"),
            "source": "OpenStreetMap (Overpass API)",
            "source_url": f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}",
        })
    for key in groups:
        groups[key] = sorted(groups[key], key=lambda row: row["distance_km"])[:limits.get(key, 10)]
    return groups, config, None


def _build_query(tag_map, latitude, longitude, radius_m):
    """Builds one combined Overpass QL query for every (key, value) pair in tag_map."""
    clauses = []
    for category, tag_pairs in tag_map.items():
        for key, value in tag_pairs:
            clauses.append(f'  nwr["{key}"="{value}"](around:{radius_m},{latitude},{longitude});')
    body = "\n".join(clauses)
    return f"[out:json][timeout:25];\n(\n{body}\n);\nout center tags;"


def _category_for_tags(tags, tag_map):
    """Given an OSM element's tags dict, finds which of our categories it matches."""
    for category, tag_pairs in tag_map.items():
        for key, value in tag_pairs:
            if tags.get(key) == value:
                return category
    return "unknown"


def _run_query(query):
    print("QUERY:")
    print(query)

    try:
        response = requests.post(
            settings.OVERPASS_API_URL,
            data={"data": query},
            headers={
                "User-Agent": "TourismApp/1.0",
                "Accept": "application/json",
            },
            timeout=90,
        )

        print("Status:", response.status_code)
        print(response.text[:500])   # Show first 500 characters

        response.raise_for_status()
        return response.json().get("elements", [])

    except (requests.RequestException, ValueError) as exc:
        print("ERROR:", exc)
        return []
def _element_coords(element):
    """
    Nodes have lat/lon directly.
    Ways and relations use the center returned by:
    out center tags;
    """
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]

    center = element.get("center")
    if center:
        return center.get("lat"), center.get("lon")

    return None, None
    
def fetch_essential_services(latitude, longitude, radius_m=1000):
    """
    Queries Overpass for hospitals, clinics, pharmacies, police, armed
    forces, fire stations, banks, ambulance services, municipality
    offices, and tourism information offices near a point.

    Returns a list of dicts: {osm_id, category, name, phone, latitude,
    longitude, address, raw_tags}. Never raises — returns [] if Overpass
    is unreachable, so callers can degrade gracefully.
    """
    query = _build_query(ESSENTIAL_SERVICE_TAGS, latitude, longitude, radius_m)
    elements = _run_query(query)

    results = []
    for element in elements:
        tags = element.get("tags", {})
        lat, lon = _element_coords(element)
        if lat is None:
            continue
        results.append({
            "osm_id": f'{element["type"]}/{element["id"]}',
            "category": _category_for_tags(tags, ESSENTIAL_SERVICE_TAGS),
            "name": tags.get("name") or tags.get("name:en") or "Unnamed",
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "latitude": lat,
            "longitude": lon,
            "address": ", ".join(filter(None, [
                tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:country"),
            ])),
            "raw_tags": tags,
        })
    return results


def fetch_tourism_places(latitude, longitude, radius_m=1000):
    """
    Queries Overpass for attractions, viewpoints, museums, hotels,
    information points, restaurants, cafes, monuments, natural peaks/
    waterfalls, and hiking paths/routes near a point.

    Returns a list of dicts: {osm_id, category, name, latitude,
    longitude, address, raw_tags}. Never raises — returns [] on failure.
    """
    query = _build_query(TOURISM_PLACE_TAGS, latitude, longitude, radius_m)
    elements = _run_query(query)

    results = []
    for element in elements:
        tags = element.get("tags", {})
        lat, lon = _element_coords(element)
        if lat is None:
            continue
        results.append({
            "osm_id": f'{element["type"]}/{element["id"]}',
            "category": _category_for_tags(tags, TOURISM_PLACE_TAGS),
            "name": tags.get("name") or tags.get("name:en") or "Unnamed",
            "latitude": lat,
            "longitude": lon,
            "address": ", ".join(filter(None, [
                tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:country"),
            ])),
            "raw_tags": tags,
        })
    return results


def sync_essential_services(latitude, longitude, radius_m=5000):
    """
    Fetches essential services from Overpass AND upserts them into the
    OSMEssentialService table (persisting, not just live pass-through —
    subsequent reads for the same area come straight from the DB, no
    repeated Overpass calls needed). Returns (created_count, updated_count).
    """
    from tourist.models import OSMEssentialService

    fetched = fetch_essential_services(latitude, longitude, radius_m)
    created, updated = 0, 0
    for item in fetched:
        _, was_created = OSMEssentialService.objects.update_or_create(
            osm_id=item["osm_id"],
            defaults={
                "category": item["category"], "name": item["name"], "phone": item["phone"],
                "latitude": item["latitude"], "longitude": item["longitude"],
                "address": item["address"], "raw_tags": item["raw_tags"],
            },
        )
        created += was_created
        updated += not was_created
    return created, updated


def sync_tourism_places(latitude, longitude, radius_m=1000):
    """
    Fetches tourism places from Overpass AND upserts them into the
    OSMTourismPlace table. Returns (created_count, updated_count).
    """
    from tourist.models import OSMTourismPlace

    fetched = fetch_tourism_places(latitude, longitude, radius_m)
    created, updated = 0, 0
    for item in fetched:
        _, was_created = OSMTourismPlace.objects.update_or_create(
            osm_id=item["osm_id"],
            defaults={
                "category": item["category"], "name": item["name"],
                "latitude": item["latitude"], "longitude": item["longitude"],
                "address": item["address"], "raw_tags": item["raw_tags"],
            },
        )
        created += was_created
        updated += not was_created
    return created, updated
