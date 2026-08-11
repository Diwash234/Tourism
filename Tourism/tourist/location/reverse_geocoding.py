"""
Reverse Geocoding Engine for Nepal Coordinates
Resolves (lat, lon) -> Nearest Municipality, District, and Province.
"""
from math import radians, sin, cos, sqrt, atan2
from .administrative_boundaries import MUNICIPALITY_COORDINATES


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def reverse_geocode(latitude: float, longitude: float) -> dict:
    """
    Finds nearest administrative body to coordinates within Nepal.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return {"district": "Kathmandu", "province": "Bagmati", "municipality": "Kathmandu Metropolitan"}

    nearest_muni = None
    min_dist = float("inf")

    for muni_name, data in MUNICIPALITY_COORDINATES.items():
        dist = _haversine(lat, lon, data["lat"], data["lng"])
        if dist < min_dist:
            min_dist = dist
            nearest_muni = (muni_name, data)

    if nearest_muni:
        name, data = nearest_muni
        return {
            "municipality": name.title(),
            "district": data["district"],
            "province": data["province"],
            "distance_km": round(min_dist, 2),
            "altitude": f"{data['alt']:,}m",
        }

    return {"district": "Kaski", "province": "Gandaki", "municipality": "Pokhara Metropolitan"}
