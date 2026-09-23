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


_DB_ANCHOR_CACHE = None


def _db_anchors():
    """City/district anchor points harvested from verified Destination rows.

    The static MUNICIPALITY_COORDINATES table only covers 31 headquarters;
    the destinations table adds a real centroid per (city, district) pair so
    reverse geocoding reflects where the user actually is instead of the
    nearest of 31 hubs. Cached per process; safe when the DB is unavailable.
    """
    global _DB_ANCHOR_CACHE
    if _DB_ANCHOR_CACHE is None:
        anchors = []
        try:
            from tourist.models import Destination

            qs = (Destination.objects.filter(is_active=True)
                  .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
                  .exclude(district__isnull=True).exclude(district="")
                  .values_list("city", "district", "province", "latitude", "longitude"))
            seen = set()
            for city, district, province, lat, lng in qs.iterator():
                key = (str(city or "").strip().lower(), str(district).strip().lower())
                if key in seen:
                    continue
                seen.add(key)
                anchors.append({
                    "municipality": str(city or "").strip(),
                    "district": str(district).strip(),
                    "province": str(province or "").strip(),
                    "lat": float(lat),
                    "lng": float(lng),
                })
        except Exception:  # noqa: BLE001 - migrations/tests without data
            anchors = []
        _DB_ANCHOR_CACHE = anchors
    return _DB_ANCHOR_CACHE


def reset_anchor_cache():
    global _DB_ANCHOR_CACHE
    _DB_ANCHOR_CACHE = None


def reverse_geocode(latitude: float, longitude: float) -> dict:
    """
    Finds nearest administrative body to coordinates within Nepal.

    Returns {} when the coordinates cannot honestly be resolved — callers
    must show "unknown" rather than a fabricated default city.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return {}

    nearest = None
    min_dist = float("inf")

    for muni_name, data in MUNICIPALITY_COORDINATES.items():
        dist = _haversine(lat, lon, data["lat"], data["lng"])
        if dist < min_dist:
            min_dist = dist
            nearest = {
                "municipality": muni_name.title(),
                "district": data["district"],
                "province": data["province"],
                "altitude": f"{data['alt']:,}m",
            }

    for anchor in _db_anchors():
        dist = _haversine(lat, lon, anchor["lat"], anchor["lng"])
        if dist < min_dist:
            min_dist = dist
            nearest = {
                "municipality": anchor["municipality"],
                "district": anchor["district"],
                "province": anchor["province"],
            }

    # Beyond ~60 km of every known anchor we cannot honestly name the place.
    if nearest is None or min_dist > 60:
        return {}

    nearest["distance_km"] = round(min_dist, 2)
    return nearest
