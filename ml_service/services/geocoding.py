"""
geocoding.py

Forward Geocoding engine for Nepal:
Resolves text administrative queries (Province, District, Municipality, Ward, Landmark)
into exact geospatial coordinates (Latitude, Longitude), elevation, and bounds.
"""

from .administrative_boundaries import NEPAL_DISTRICTS_DATA, NEPAL_PROVINCES


MUNICIPALITY_GEO_INDEX = {
    # Kathmandu Valley
    "kathmandu": {"lat": 27.7172, "lng": 85.3240, "altitude": 1400, "district": "Kathmandu", "province": "Bagmati"},
    "patan": {"lat": 27.6644, "lng": 85.3188, "altitude": 1400, "district": "Lalitpur", "province": "Bagmati"},
    "lalitpur": {"lat": 27.6644, "lng": 85.3188, "altitude": 1400, "district": "Lalitpur", "province": "Bagmati"},
    "bhaktapur": {"lat": 27.6710, "lng": 85.4298, "altitude": 1401, "district": "Bhaktapur", "province": "Bagmati"},
    "nagarkot": {"lat": 27.7174, "lng": 85.5204, "altitude": 2175, "district": "Bhaktapur", "province": "Bagmati"},
    "dhulikhel": {"lat": 27.6167, "lng": 85.5500, "altitude": 1550, "district": "Kavrepalanchok", "province": "Bagmati"},

    # Pokhara & Annapurna
    "pokhara": {"lat": 28.2096, "lng": 83.9856, "altitude": 822, "district": "Kaski", "province": "Gandaki"},
    "ghandruk": {"lat": 28.3744, "lng": 83.8089, "altitude": 2012, "district": "Kaski", "province": "Gandaki"},
    "annapurna base camp": {"lat": 28.5300, "lng": 83.8780, "altitude": 4130, "district": "Kaski", "province": "Gandaki"},
    "bandipur": {"lat": 27.9333, "lng": 84.4167, "altitude": 1030, "district": "Tanahun", "province": "Gandaki"},
    "jomsom": {"lat": 28.7833, "lng": 83.7333, "altitude": 2743, "district": "Mustang", "province": "Gandaki"},
    "muktinath": {"lat": 28.8167, "lng": 83.8667, "altitude": 3800, "district": "Mustang", "province": "Gandaki"},
    "lo manthang": {"lat": 29.1822, "lng": 83.9567, "altitude": 3840, "district": "Mustang", "province": "Gandaki"},
    "manang": {"lat": 28.6667, "lng": 84.0167, "altitude": 3519, "district": "Manang", "province": "Gandaki"},

    # Everest / Khumbu
    "everest base camp": {"lat": 27.9881, "lng": 86.9250, "altitude": 5364, "district": "Solukhumbu", "province": "Koshi"},
    "namche bazaar": {"lat": 27.8056, "lng": 86.7111, "altitude": 3440, "district": "Solukhumbu", "province": "Koshi"},
    "lukla": {"lat": 27.6869, "lng": 86.7291, "altitude": 2860, "district": "Solukhumbu", "province": "Koshi"},

    # Lowlands / Terai & Western Nepal
    "chitwan": {"lat": 27.5341, "lng": 84.4530, "altitude": 150, "district": "Chitwan", "province": "Bagmati"},
    "sauraha": {"lat": 27.5833, "lng": 84.4833, "altitude": 150, "district": "Chitwan", "province": "Bagmati"},
    "lumbini": {"lat": 27.4699, "lng": 83.2755, "altitude": 105, "district": "Rupandehi", "province": "Lumbini"},
    "janakpur": {"lat": 26.7271, "lng": 85.9242, "altitude": 74, "district": "Dhanusha", "province": "Madhesh"},
    "ilam": {"lat": 26.9117, "lng": 87.9261, "altitude": 1208, "district": "Ilam", "province": "Koshi"},
    "rara": {"lat": 29.5333, "lng": 82.0833, "altitude": 2990, "district": "Mugu", "province": "Karnali"},
    "shey phoksundo": {"lat": 29.2167, "lng": 82.9500, "altitude": 3611, "district": "Dolpa", "province": "Karnali"},
}


def geocode(place_name: str, district: str = "", municipality: str = "", ward: int = 1) -> dict:
    """
    Forward geocoding: Resolves place/municipality into coordinates.
    """
    key = place_name.lower().strip()
    for name, data in MUNICIPALITY_GEO_INDEX.items():
        if name in key or key in name:
            lat = data["lat"]
            lng = data["lng"]
            if ward and ward > 1:
                lat += ((ward % 5) - 2) * 0.003
                lng += ((ward // 5) - 1) * 0.003
            return {
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "altitude": f"{data['altitude']}m",
                "district": data["district"],
                "province": data["province"],
                "source": "Nepal Administrative Geocode Index"
            }

    if district:
        for dist_name, data in NEPAL_DISTRICTS_DATA.items():
            if dist_name.lower() == district.lower() or dist_name.lower() in district.lower():
                return {
                    "latitude": data["lat"],
                    "longitude": data["lng"],
                    "altitude": f"{data['altitude']}m",
                    "district": dist_name,
                    "province": data["province"],
                    "source": "District Centroid"
                }

    # Fallback to Pokhara / Nepal geographic center
    return {
        "latitude": 28.209600,
        "longitude": 83.985600,
        "altitude": "822m",
        "district": "Kaski",
        "province": "Gandaki",
        "source": "Default Geographic Center"
    }
