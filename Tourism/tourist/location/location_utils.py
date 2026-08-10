"""
Spatial & Geodetic Utility Helpers for Nepal Tourism Portal
"""
from math import radians, sin, cos, sqrt, atan2
from decimal import Decimal


def haversine_distance_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(R * c, 2)
    except (ValueError, TypeError):
        return 0.0


def bounding_box_coords(latitude: float, longitude: float, radius_km: float = 25.0) -> dict:
    R = 6371.0
    lat, lon = float(latitude), float(longitude)
    d_lat = radius_km / R * (180.0 / 3.1415926535)
    d_lon = radius_km / (R * cos(radians(lat))) * (180.0 / 3.1415926535)
    return {
        "min_lat": lat - d_lat,
        "max_lat": lat + d_lat,
        "min_lon": lon - d_lon,
        "max_lon": lon + d_lon,
    }
