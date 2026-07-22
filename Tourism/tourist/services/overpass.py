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
