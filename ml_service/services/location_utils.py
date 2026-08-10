"""
location_utils.py

Geospatial, mathematical, and terrain calculations for Nepal Tourism:
- Haversine Distance (km & miles)
- Compass Bearing (degrees and 16-point cardinal compass)
- Turn Direction Angle for GTA/Free Fire Game Navigation
- Altitude Sickness (AMS) Hazard Scoring based on elevation
- Bounding Box generation for radial search
"""

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> dict:
    """Calculate compass heading angle in degrees (0-360) and 16-wind compass point."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlon_r = math.radians(lon2 - lon1)

    y = math.sin(dlon_r) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r)

    initial_bearing = math.degrees(math.atan2(y, x))
    compass_heading = (initial_bearing + 360) % 360

    cardinals = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    idx = round(compass_heading / (360.0 / len(cardinals))) % len(cardinals)

    return {
        "degrees": round(compass_heading, 1),
        "cardinal": cardinals[idx],
        "label": f"{round(compass_heading)}° {cardinals[idx]}"
    }


def calculate_turn_direction(bearing_initial: float, bearing_next: float) -> str:
    """Computes navigation turn maneuver: straight, left, right, sharp_left, sharp_right, uturn."""
    angle_diff = (bearing_next - bearing_initial + 180) % 360 - 180
    if -25 <= angle_diff <= 25:
        return "straight"
    elif 25 < angle_diff <= 80:
        return "right"
    elif 80 < angle_diff <= 140:
        return "sharp_right"
    elif -80 <= angle_diff < -25:
        return "left"
    elif -140 <= angle_diff < -80:
        return "sharp_left"
    else:
        return "uturn"


def estimate_altitude_risk(altitude_meters: int) -> dict:
    """
    Evaluates acute mountain sickness (AMS) risk based on elevation.
    Nepal elevations:
      < 2500m: Low risk
      2500m - 3500m: Moderate risk (Acclimatization threshold)
      3500m - 5000m: High risk (Everest Base Camp / ABC / Thorong La)
      > 5000m: Extreme high altitude
    """
    if altitude_meters < 2500:
        return {
            "risk_level": "LOW",
            "score": 10,
            "category": "Safe Elevation",
            "advice": "Normal trekking precautions; no acclimatization rest day strictly required."
        }
    elif 2500 <= altitude_meters < 3500:
        return {
            "risk_level": "MODERATE",
            "score": 35,
            "category": "Acclimatization Recommended",
            "advice": "Ascend no more than 500m per day. Drink 3-4 liters of water daily. Rest in Namche/Manang."
        }
    elif 3500 <= altitude_meters < 5000:
        return {
            "risk_level": "HIGH",
            "score": 70,
            "category": "High Altitude Warning",
            "advice": "Mandatory acclimatization rest day. Watch for headaches, dizziness. Carry Diamox and descend if symptoms persist."
        }
    else:
        return {
            "risk_level": "CRITICAL",
            "score": 90,
            "category": "Extreme High Altitude",
            "advice": "Extreme oxygen depletion zone. Certified mountain guide and emergency helicopter rescue insurance required."
        }


def bounding_box(lat: float, lon: float, radius_km: float) -> dict:
    """Computes a bounding box of lat/lng limits around a coordinate."""
    lat_r = math.radians(lat)
    deg_lat = radius_km / 111.0
    deg_lon = radius_km / (111.0 * math.cos(lat_r))
    return {
        "min_lat": lat - deg_lat,
        "max_lat": lat + deg_lat,
        "min_lon": lon - deg_lon,
        "max_lon": lon + deg_lon,
    }
