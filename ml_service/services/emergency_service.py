"""
services/emergency_service.py

Emergency nearby places service.
Loads hospital and police CSV datasets
and finds nearest facilities using GPS.
"""

import csv
import heapq
import logging
from itertools import chain
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path

# --------------------------------------------------



BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
    / "Tourism"
    / "dataset"
)



HOSPITAL_FILE = BASE_DIR / "hospital_cleaned.csv"



POLICE_FILE = BASE_DIR / "police_station_cleaned.csv"



logger = logging.getLogger(__name__)

# --------------------------------------------------
# Distance calculation
# --------------------------------------------------

def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371


    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))


    dlat = lat2 - lat1
    dlon = lon2 - lon1


    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        *
        cos(lat2)
        *
        sin(dlon / 2) ** 2
    )


    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )


    return R * c



# --------------------------------------------------
# CSV streaming
# --------------------------------------------------

def _iter_facilities(path, facility_type, latitude, longitude):
    if not path.is_file():
        logger.warning("Emergency facility dataset not found: %s", path)
        return

    name_column = "hospital_name" if facility_type == "hospital" else "police_station"
    with path.open(newline="", encoding="utf-8-sig") as source:
        for place in csv.DictReader(source):
            try:
                place_lat = float(place["latitude"])
                place_lon = float(place["longitude"])
            except (KeyError, TypeError, ValueError):
                continue

            yield {
                "type": facility_type,
                "name": place.get(name_column) or (
                    "Unknown Hospital" if facility_type == "hospital" else "Unknown Police Station"
                ),
                "phone": place.get("phone") or "",
                "address": place.get("address") or "",
                "district": place.get("district") or "",
                "province": place.get("province") or "",
                "latitude": place_lat,
                "longitude": place_lon,
                "distance_km": round(haversine_km(latitude, longitude, place_lat, place_lon), 2),
            }



# --------------------------------------------------
# Find nearest facilities
# --------------------------------------------------

def nearest_facilities(
    latitude,
    longitude,
    category=None,
    limit=5
):
    limit = max(1, min(int(limit), 50))
    if category and category not in {"hospital", "police_station"}:
        return []
    facility_types = [category] if category else ["hospital", "police_station"]
    files = {
        "hospital": HOSPITAL_FILE,
        "police_station": POLICE_FILE,
    }
    candidates = chain.from_iterable(
        _iter_facilities(files[kind], kind, latitude, longitude)
        for kind in facility_types
    )
    return heapq.nsmallest(limit, candidates, key=lambda place: place["distance_km"])



# --------------------------------------------------
# Emergency contacts
# --------------------------------------------------

def get_nearest_emergency_contacts(
    latitude,
    longitude
):


    hospitals = nearest_facilities(
        latitude,
        longitude,
        category="hospital",
        limit=3
    )


    police = nearest_facilities(
        latitude,
        longitude,
        category="police_station",
        limit=3
    )


    return {

        "hospitals": hospitals,

        "police_stations": police

    }
