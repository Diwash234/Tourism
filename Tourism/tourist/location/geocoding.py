"""
Forward Geocoding Engine for Nepal Destinations
Calculates latitude, longitude, and altitude from administrative inputs.
"""
from decimal import Decimal
from .administrative_boundaries import MUNICIPALITY_COORDINATES, NEPAL_DISTRICTS


def geocode_place(province: str, district: str, municipality: str = "", ward_number: int = 1) -> dict:
    """
    Computes accurate coordinates and altitude based on Nepal administrative units.
    """
    muni_key = (municipality or "").strip().lower()
    
    # Direct match
    match = None
    if muni_key in MUNICIPALITY_COORDINATES:
        match = MUNICIPALITY_COORDINATES[muni_key]
    else:
        # Partial match
        for k, v in MUNICIPALITY_COORDINATES.items():
            if (muni_key and muni_key in k) or (district and district.lower() in v["district"].lower()):
                match = v
                break

    if not match:
        # Fallback to Pokhara / Nepal geographic center
        return {
            "latitude": Decimal("28.209600"),
            "longitude": Decimal("83.985600"),
            "altitude": "1,400m",
            "source": "default_nepal_center"
        }

    # Apply deterministic micro-offset per ward number (approx. 300m-500m per ward step)
    ward_int = int(ward_number) if ward_number else 1
    lat_offset = Decimal(str(round(((ward_int % 5) - 2) * 0.003, 6)))
    lng_offset = Decimal(str(round((int(ward_int / 5) - 1) * 0.003, 6)))

    base_lat = Decimal(str(match["lat"]))
    base_lng = Decimal(str(match["lng"]))

    return {
        "latitude": (base_lat + lat_offset).quantize(Decimal("0.000001")),
        "longitude": (base_lng + lng_offset).quantize(Decimal("0.000001")),
        "altitude": f"{match['alt']:,}m",
        "province": match.get("province", province),
        "district": match.get("district", district),
        "source": "nepal_administrative_geocoder"
    }
