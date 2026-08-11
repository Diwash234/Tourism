"""
reverse_geocoding.py

Reverse Geocoding engine for Nepal:
Converts raw (latitude, longitude) coordinates into nearest administrative
District, Province, City, and landmark location.
"""

from .administrative_boundaries import NEPAL_DISTRICTS_DATA
from .location_utils import haversine_km


def reverse_geocode(latitude: float, longitude: float) -> dict:
    """
    Finds the nearest Nepal District, Province, and Region for a given lat/lng.
    """
    nearest_district = None
    min_dist = float("inf")

    for district_name, data in NEPAL_DISTRICTS_DATA.items():
        dist = haversine_km(latitude, longitude, data["lat"], data["lng"])
        if dist < min_dist:
            min_dist = dist
            nearest_district = {"district": district_name, "distance_km": dist, **data}

    if nearest_district:
        return {
            "country": "Nepal",
            "province": nearest_district["province"],
            "district": nearest_district["district"],
            "city": nearest_district["district"],
            "approx_altitude": f"{nearest_district['altitude']}m",
            "distance_to_center_km": nearest_district["distance_km"],
        }

    return {
        "country": "Nepal",
        "province": "Gandaki",
        "district": "Kaski",
        "city": "Pokhara",
        "approx_altitude": "822m",
        "distance_to_center_km": 0,
    }
