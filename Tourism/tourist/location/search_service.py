"""
LocationSearchService — Universal Geographic & Tourism Search Engine for Nepal.
Searches verified tourism destinations, local services (banks, ATMs, pharmacies, stores,
hospitals, police, restaurants, hotels, gas stations), administrative hubs, and arbitrary
places (e.g. Lakeside, Thamel, Pokhara, Tribhuvan Airport).
"""
import re
import math
from django.db.models import Q
from .administrative_boundaries import MUNICIPALITY_COORDINATES
from .location_utils import haversine_distance_km

POKHARA_CENTER = (28.2096, 83.9856)
KATHMANDU_CENTER = (27.7172, 85.3240)

# Well-known Nepal landmark coordinates fallback dict
# Resolver variant tables: Nepali generic words transliterated to their English
# equivalents, and trailing locality tokens that may be stripped before a
# second exact DB lookup ("Mahendra Cave Pokhara" -> "Mahendra Cave",
# "Mahendra Gufa" -> "Mahendra Cave").
NEPALI_TO_ENGLISH_WORDS = {
    "gufa": "cave", "tal": "lake", "pokhari": "lake", "daha": "lake",
    "jharana": "waterfall", "jharna": "waterfall", "mandir": "temple",
    "deval": "temple", "danda": "hill", "pul": "bridge", "bazar": "bazaar",
}
LOCALITY_SUFFIX_WORDS = {
    "pokhara", "kathmandu", "lalitpur", "bhaktapur", "butwal", "chitwan",
    "bharatpur", "biratnagar", "janakpur", "dharan", "hetauda", "itahari",
    "nepalgunj", "dhangadhi", "damak", "kaski", "nepal",
}

NEPAL_LANDMARKS = {
    "lakeside": {"name": "Lakeside, Pokhara", "lat": 28.2096, "lng": 83.9856, "city": "Pokhara", "district": "Kaski", "province": "Gandaki"},
    "thamel": {"name": "Thamel, Kathmandu", "lat": 27.7152, "lng": 85.3123, "city": "Kathmandu", "district": "Kathmandu", "province": "Bagmati"},
    "phewa lake": {"name": "Phewa Lake, Pokhara", "lat": 28.2117, "lng": 83.9517, "city": "Pokhara", "district": "Kaski", "province": "Gandaki"},
    "fewa lake": {"name": "Fewa Lake, Pokhara", "lat": 28.2117, "lng": 83.9517, "city": "Pokhara", "district": "Kaski", "province": "Gandaki"},
    "tribhuvan airport": {"name": "Tribhuvan International Airport", "lat": 27.6966, "lng": 85.3591, "city": "Kathmandu", "district": "Kathmandu", "province": "Bagmati"},
    "pokhara airport": {"name": "Pokhara International Airport", "lat": 28.1994, "lng": 83.9822, "city": "Pokhara", "district": "Kaski", "province": "Gandaki"},
    "sarangkot": {"name": "Sarangkot Sunrise Viewpoint", "lat": 28.2439, "lng": 83.9486, "city": "Pokhara", "district": "Kaski", "province": "Gandaki"},
    "pashupatinath": {"name": "Pashupatinath Temple", "lat": 27.7104, "lng": 85.3487, "city": "Kathmandu", "district": "Kathmandu", "province": "Bagmati"},
    "boudhanath": {"name": "Boudhanath Stupa", "lat": 27.7215, "lng": 85.3620, "city": "Kathmandu", "district": "Kathmandu", "province": "Bagmati"},
    "swayambhunath": {"name": "Swayambhunath Stupa (Monkey Temple)", "lat": 27.7149, "lng": 85.2904, "city": "Kathmandu", "district": "Kathmandu", "province": "Bagmati"},
    "patan durbar square": {"name": "Patan Durbar Square", "lat": 27.6727, "lng": 85.3253, "city": "Lalitpur", "district": "Lalitpur", "province": "Bagmati"},
    "bhaktapur durbar square": {"name": "Bhaktapur Durbar Square", "lat": 27.6722, "lng": 85.4284, "city": "Bhaktapur", "district": "Bhaktapur", "province": "Bagmati"},
    "lumbini": {"name": "Lumbini Sacred Garden", "lat": 27.4800, "lng": 83.2750, "city": "Lumbini", "district": "Rupandehi", "province": "Lumbini"},
    "chitwan": {"name": "Chitwan National Park (Sauraha)", "lat": 27.5777, "lng": 84.4994, "city": "Sauraha", "district": "Chitwan", "province": "Bagmati"},
    "nagarkot": {"name": "Nagarkot Himalayan Sunrise Viewpoint", "lat": 27.7174, "lng": 85.5212, "city": "Nagarkot", "district": "Bhaktapur", "province": "Bagmati"},
}



def _safe_image_url(field):
    """Return a URL string for an ImageField without ever opening the file.

    A raw FieldFile in a JSON payload makes DRF read the file from storage
    (500 when the media file is missing), and an empty field raises on .url.
    Some legacy rows stored an external URL as the file name — restore those
    to a usable absolute URL instead of a broken /media/https:/... path.
    """
    try:
        if not field:
            return ""
        name = getattr(field, "name", "") or ""
        if name.startswith(("http://", "https://")):
            return name
        if name.startswith("https:/"):
            return "https://" + name[len("https:/"):]
        if name.startswith("http:/"):
            return "http://" + name[len("http:/"):]
        return field.url or ""
    except (ValueError, AttributeError):
        return ""


def compute_bearing(lat1, lng1, lat2, lng2):
    """Calculates compass bearing in degrees and 8-cardinal direction text."""
    try:
        y = math.sin(math.radians(lng2 - lng1)) * math.cos(math.radians(lat2))
        x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lng2 - lng1))
        deg = (math.atan2(y, x) * 180 / math.pi + 360) % 360
        dirs = [("N", "⬆"), ("NE", "↗"), ("E", "➔"), ("SE", "↘"), ("S", "⬇"), ("SW", "↙"), ("W", "⬅"), ("NW", "↖")]
        idx = int((deg + 22.5) // 45) % 8
        return round(deg, 1), dirs[idx][0], dirs[idx][1]
    except Exception:
        return 0.0, "N", "⬆"


# ---------------------------------------------------------------------------
# Live OpenStreetMap fill — "places that exist outside our database".
#
# Overpass scans every tagged point inside a circle, so a country-sized radius
# would time out instead of answering; a nearby search is well under this cap.
# ---------------------------------------------------------------------------
LIVE_OSM_MAX_RADIUS_KM = 50.0
LIVE_OSM_CACHE_TTL = 900  # seconds, per (area, radius, category)
# The live call is inline with an API request, so its mirror-failover budget is
# deliberately small: an unreachable provider costs at most this long before the
# recorded rows are served as-is. Empty results are cached for less time so a
# provider that comes back (or goes down) is picked up sooner than 15 minutes.
LIVE_OSM_TIMEOUT_S = 5
LIVE_OSM_EMPTY_TTL = 300

# Our category filter -> the OSM tag values that mean the same place. A
# category we cannot honour maps to an empty set on purpose: returning every
# mapped point under a wrong "pharmacy" tab would be worse than returning
# none, so an unknown category simply gets no live rows.
_LIVE_OSM_CATEGORY_ALIASES = {
    "hotel": {"hotel", "hostel", "guest_house", "motel", "apartment", "resort", "chalet"},
    "hotels": {"hotel", "hostel", "guest_house", "motel", "apartment", "resort", "chalet"},
    "restaurant": {"restaurant", "fast_food", "food_court"},
    "restaurants": {"restaurant", "fast_food", "food_court"},
    "cafe": {"cafe", "bar", "pub"},
    "cafes": {"cafe", "bar", "pub"},
    "bank": {"bank"},
    "banks": {"bank"},
    "atm": {"atm"},
    "atms": {"atm"},
    "hospital": {"hospital", "clinic", "doctors"},
    "hospitals": {"hospital", "clinic", "doctors"},
    "police": {"police"},
    "pharmacy": {"pharmacy", "chemist"},
    "pharmacies": {"pharmacy", "chemist"},
    "gas_station": {"fuel"},
    "attraction": {"attraction", "artwork", "theme_park", "zoo", "gallery", "information"},
    "attractions": {"attraction", "artwork", "theme_park", "zoo", "gallery", "information"},
    "viewpoint": {"viewpoint"},
    "viewpoints": {"viewpoint"},
    "museum": {"museum"},
    "temples": {"place_of_worship"},
    "temple": {"place_of_worship"},
}


def _live_osm_nearby(ref_lat, ref_lng, radius_km, cat_filter=""):
    """OpenStreetMap tourism/amenity points near a point, in the raw row shape
    ``search_places`` builds before distance ranking (so the caller's normal
    loop adds distance, bearing and dedupe for free).

    Honest by construction: every row carries ``source: "openstreetmap_live"``
    plus its OSM id/url, and the function NEVER raises — an unreachable
    provider returns [] and the recorded database answer is served unchanged.
    """
    from django.conf import settings

    if not getattr(settings, "NEARBY_LIVE_OSM", False):
        return []
    try:
        radius_km = float(radius_km)
    except (TypeError, ValueError):
        return []
    if not radius_km or radius_km > LIVE_OSM_MAX_RADIUS_KM:
        return []
    cat_filter = (cat_filter or "").strip().lower()
    wanted = _LIVE_OSM_CATEGORY_ALIASES.get(cat_filter, set() if cat_filter else None)
    if cat_filter and not wanted:
        return []

    import hashlib
    from django.core.cache import cache

    key = "place-live-osm:" + hashlib.sha256(
        f"{round(float(ref_lat), 3)}|{round(float(ref_lng), 3)}|{radius_km:.2f}|{cat_filter}".encode()
    ).hexdigest()
    try:
        cached = cache.get(key)
    except Exception:  # a broken cache backend must not break search
        cached = None
    if cached is not None:
        return cached

    from tourist.utils import overpass_search_nearby

    try:
        # Both tourism and amenity nodes: hotels and restaurants aside, a
        # nearby list is worthless if it omits banks, ATMs and pharmacies.
        raw = overpass_search_nearby(
            ref_lat, ref_lng, radius_m=max(50, int(radius_km * 1000)),
            tourism_only=False, timeout=LIVE_OSM_TIMEOUT_S,
        )
    except Exception:
        raw = []

    rows = []
    for item in raw or []:
        lat, lng = item.get("latitude"), item.get("longitude")
        if lat is None or lng is None:
            continue
        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            continue
        name = str(item.get("name") or "").strip()
        if not name or name == "Unnamed":
            continue
        kind = str(item.get("type") or "").strip().lower()
        if wanted is not None and kind not in wanted:
            continue
        tags = item.get("tags") or {}
        rows.append({
            "id": f"live-{item.get('osm_id')}",
            "osm_id": item.get("osm_id"),
            "name": name,
            "category": (kind or "Place").replace("_", " ").title(),
            "type": kind or "place",
            "latitude": lat,
            "longitude": lng,
            "address": ", ".join(
                part for part in [tags.get("addr:street"), tags.get("addr:city")] if part
            ) or "Nepal",
            "city": tags.get("addr:city") or "",
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "website": tags.get("website") or tags.get("contact:website") or "",
            "opening_hours": tags.get("opening_hours") or "",
            "source": "openstreetmap_live",
            "source_url": f"https://www.openstreetmap.org/node/{item.get('osm_id')}",
            "is_destination": False,
        })

    try:
        cache.set(key, rows, LIVE_OSM_CACHE_TTL if rows else LIVE_OSM_EMPTY_TTL)
    except Exception:
        pass
    return rows


class LocationSearchService:
    @staticmethod
    def search_places(query="", user_lat=None, user_lng=None, category=None, radius_km=50, limit=25):
        """
        Unified Place Search engine:
        Searches Destination, Hospital, PoliceStation, Restaurant, Hotel, OSMEssentialService,
        OSMTourismPlace, and Nepal Administrative Landmarks.
        """
        q = (query or "").strip().lower()
        cleaned_q = re.sub(r"\b(nearest|near|me|find|search|the|a|an)\b", "", q).strip()
        search_term = cleaned_q or q

        # Owner field-lists often spell places with a generic geographic word
        # ("Bandipur Bazaar", "Swargadwari Temple", "Gangapurna Lake",
        # "Chandragiri Hills") while the DB stores only the core name. Keep the
        # full phrase AND add a variant with generic words stripped, so those
        # spellings still find the right place (live gap: 8/8 owner spellings
        # returned NOTHING while the places existed).
        _GENERIC_WORDS = (
            r"bazaar|bazar|temple|mandir|monastery|gompa|lake|pokhari|pond|river|himal|"
            r"waterfall|jharana|jharna|falls|hills|hill|danda|daha|cave|gufa|stupa|"
            r"durbar|palace|park|viewpoint|base camp|trek|dham|deurali"
        )
        stripped = re.sub(r"\b(%s)\b" % _GENERIC_WORDS, "", search_term)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        search_terms = [search_term]
        if stripped and stripped != search_term and len(stripped) >= 4:
            search_terms.append(stripped)

        def _match(*fields):
            cond = Q()
            for term in search_terms:
                for field in fields:
                    cond |= Q(**{f"{field}__icontains": term})
            return cond

        # A query like "Bandipur Eco Hotel" must be name-matched inside the
        # provider table even though the word "hotel" also selects the hotel
        # category — skipping the name filter there returned 40 arbitrary
        # rows and the named hotel was missing from its own search (live bug,
        # 2026-09-21 consolidation round). Only bare generic category words
        # keep the no-name-filter "nearest list" behaviour.
        _GENERIC_CATEGORY_TERMS = {
            "hotel", "hotels", "lodge", "lodges", "resort", "resorts", "hostel",
            "hostels", "homestay", "homestays", "restaurant", "restaurants",
            "cafe", "cafes", "food", "dining", "eatery", "bank", "banks",
            "atm", "atms", "hospital", "hospitals", "clinic", "clinics",
            "police", "pharmacy", "pharmacies", "store", "stores", "shop",
            "shops", "mart", "marts", "supermarket", "supermarkets", "gas",
            "fuel", "petrol", "bus", "buses", "station", "stations", "stop",
            "stops",
        }
        _term_norm = re.sub(r"[^a-z0-9]", "", search_term)
        _name_query = bool(_term_norm) and len(_term_norm) >= 4 and _term_norm not in _GENERIC_CATEGORY_TERMS

        # Detect category intents (e.g. "bank", "atm", "hospital", "pharmacy", "police", "store")
        cat_filter = (category or "").strip().lower()
        # Normalize plural/UI tab ids to canonical provider keys, so a tab like
        # "hospitals" reaches the curated Hospital provider instead of falling
        # through to a generic destination dump (live regression, increment 6).
        _CAT_ALIASES = {
            "hospitals": "hospital", "clinics": "hospital",
            "police stations": "police",
            "hotels": "hotel", "lodges": "hotel",
            "restaurants": "restaurant",
            "cafes": "cafe",
            "banks": "bank", "atms": "atm",
            "pharmacies": "pharmacy",
            "stores": "store", "marts": "store", "supermarkets": "store",
            "gas": "gas_station", "fuel": "gas_station", "petrol pumps": "gas_station",
            "bus": "bus_stop", "bus stops": "bus_stop",
            "attractions": "attraction", "temples": "temple",
            "waterfalls": "waterfall", "viewpoints": "viewpoint",
        }
        cat_filter = _CAT_ALIASES.get(cat_filter, cat_filter)
        if not cat_filter:
            if re.search(r"\b(bank|atm|money)\b", q): cat_filter = "bank"
            elif re.search(r"\b(hospital|clinic|doctor|medical|health)\b", q): cat_filter = "hospital"
            elif re.search(r"\b(police|cop|security|station)\b", q): cat_filter = "police"
            elif re.search(r"\b(pharmacy|drugstore|chemist|medicine)\b", q): cat_filter = "pharmacy"
            elif re.search(r"\b(store|shop|mart|supermarket|grocery)\b", q): cat_filter = "store"
            elif re.search(r"\b(restaurant|food|dining|cafe|eatery)\b", q): cat_filter = "restaurant"
            elif re.search(r"\b(hotel|lodge|resort|stay|hostel)\b", q): cat_filter = "hotel"
            elif re.search(r"\b(gas|fuel|petrol|charging)\b", q): cat_filter = "gas_station"
            elif re.search(r"\b(bus|station|stop|transit)\b", q): cat_filter = "bus_stop"

        ref_lat = float(user_lat) if user_lat is not None else POKHARA_CENTER[0]
        ref_lng = float(user_lng) if user_lng is not None else POKHARA_CENTER[1]
        has_gps = (user_lat is not None and user_lng is not None)

        # Bounding-box prefilter for curated providers: without it the [:N]
        # querysets slice in arbitrary DB order and can miss every row that
        # is actually inside the radius (live bug: "hotels near Pokhara" -> 0
        # results while 1600+ hotels exist).
        import math as _math

        def _in_radius(qs):
            if not (has_gps and radius_km):
                return qs
            dlat = radius_km / 111.0
            dlng = radius_km / (111.0 * max(0.05, _math.cos(_math.radians(ref_lat))))
            return qs.filter(
                latitude__gte=ref_lat - dlat, latitude__lte=ref_lat + dlat,
                longitude__gte=ref_lng - dlng, longitude__lte=ref_lng + dlng,
            )

        raw_results = []

        # 1. Search Destination model
        from tourist.models import (
            Destination, Hotel, Restaurant, Hospital, PoliceStation,
            OSMEssentialService, OSMTourismPlace
        )

        dest_qs = Destination.objects.filter(is_active=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        # Destination-type categories filter the curated table by category name;
        # any OTHER category filter must never leak arbitrary destinations into
        # a "nearby hospitals/hotels" result list.
        _DEST_CATS = {"attraction", "temple", "nature", "waterfall", "viewpoint", "heritage"}
        if search_term and not cat_filter:
            dest_qs = dest_qs.filter(_match("name", "city", "district", "slug"))
        elif cat_filter:
            if cat_filter in _DEST_CATS:
                dest_qs = dest_qs.filter(category__name__icontains=cat_filter)
            else:
                dest_qs = dest_qs.none()

        dest_qs = _in_radius(dest_qs)
        for d in dest_qs[:60]:
            raw_results.append({
                "id": f"dest-{d.id}",
                "destination_id": d.id,
                "name": d.name,
                "category": d.category.name if getattr(d, "category", None) else "Tourism Destination",
                "type": "destination",
                "latitude": float(d.latitude),
                "longitude": float(d.longitude),
                "address": f"{d.city or ''}, {d.district or 'Nepal'}".strip(", "),
                "city": d.city or "Pokhara",
                "slug": d.slug,
                "image_url": _safe_image_url(d.cover_image),
                "source": "verified_database",
                "is_destination": True,
            })

        # 2. Search OSMEssentialService (Banks, ATMs, Pharmacies, Stores, Gas Stations, etc.)
        # Anonymous OSM nodes imported without a name are carried as
        # "<Category> (name not recorded in OSM)" — a real, located facility
        # but not a nameable place; keep them out of user-facing lists.
        osm_qs = OSMEssentialService.objects.exclude(is_archived=True).exclude(
            name__icontains="name not recorded")
        if cat_filter:
            osm_qs = osm_qs.filter(category__icontains=cat_filter)
        elif search_term:
            osm_qs = osm_qs.filter(_match("name", "address", "category"))

        osm_qs = _in_radius(osm_qs)
        for s in osm_qs[:60]:
            raw_results.append({
                "id": f"osm-{s.id}",
                "name": s.name,
                "category": s.category.replace("_", " ").title(),
                "latitude": float(s.latitude),
                "longitude": float(s.longitude),
                # DEF-021: OSMEssentialService has no `district` field — never
                # assumed one existed (crashed the whole nearby/search response
                # whenever a DB-backed row without .district was serialised).
                "address": s.address or "Nepal",
                "city": getattr(s, "district", "") or "",
                "phone": s.phone or "",
                "image_url": _safe_image_url(s.image),
                "source": "osm_essential_service",
                "is_destination": False,
            })

        # 2b. OSMTourismPlace — attractions, viewpoints, museums, waterfalls,
        # cafes, peaks and hiking routes synced from OpenStreetMap into our
        # own tables. The module docstring promised this provider but it was
        # never queried, so a nearby/search request silently omitted every
        # tourism point that is not a Destination or Hotel row — "all places
        # near me" came back empty while these rows sat in the database.
        _OSM_TP_CATS = {
            "attraction", "viewpoint", "museum", "cafe", "monument", "peak",
            "waterfall", "hiking_path", "hiking_route", "information",
        }
        if not cat_filter or cat_filter in _OSM_TP_CATS:
            tp_qs = OSMTourismPlace.objects.exclude(name__icontains="name not recorded")
            if cat_filter:
                tp_qs = tp_qs.filter(category=cat_filter)
            elif search_term:
                tp_qs = tp_qs.filter(_match("name", "address", "category"))
            for tp in _in_radius(tp_qs)[:40]:
                raw_results.append({
                    "id": f"osmtp-{tp.id}",
                    "name": tp.name,
                    "category": tp.get_category_display(),
                    "type": tp.category,
                    "latitude": float(tp.latitude),
                    "longitude": float(tp.longitude),
                    "address": tp.address or "Nepal",
                    "city": "",
                    "phone": (tp.raw_tags or {}).get("phone", "") if isinstance(tp.raw_tags, dict) else "",
                    "source": "osm_tourism_place",
                    "is_destination": False,
                })

        # 3. Search Hospitals & Police Stations
        if not cat_filter or cat_filter == "hospital":
            h_qs = Hospital.objects.all()
            if _name_query:
                h_qs = h_qs.filter(_match("name", "address"))
            h_qs = _in_radius(h_qs)
            for h in h_qs[:40]:
                raw_results.append({
                    "id": f"hosp-{h.id}",
                    "name": h.name,
                    "category": "Hospital",
                    "latitude": float(h.latitude),
                    "longitude": float(h.longitude),
                    "address": h.address or "Nepal",
                    "city": h.destination.city if getattr(h, "destination", None) else "Pokhara",
                    "phone": h.phone or "",
                    "source": "verified_hospital",
                    "is_destination": False,
                    # Coordinate provenance: a lat/lng copied from the parent
                    # destination is an area point, not this hospital's door.
                    "is_approximate": bool(getattr(h, "is_approximate_coordinate", False)),
                })

        if not cat_filter or cat_filter == "police":
            p_qs = PoliceStation.objects.all()
            if _name_query:
                p_qs = p_qs.filter(_match("name", "address"))
            p_qs = _in_radius(p_qs)
            for p in p_qs[:40]:
                raw_results.append({
                    "id": f"pol-{p.id}",
                    "name": p.name,
                    "category": "Police Station",
                    "latitude": float(p.latitude),
                    "longitude": float(p.longitude),
                    "address": p.address or "Nepal",
                    "city": p.destination.city if getattr(p, "destination", None) else "Pokhara",
                    "phone": p.phone or "",
                    "source": "verified_police",
                    "is_destination": False,
                    "is_approximate": bool(getattr(p, "is_approximate_coordinate", False)),
                })

        # 4. Search Hotels & Restaurants
        if not cat_filter or cat_filter == "hotel":
            ht_qs = Hotel.objects.filter(is_active=True).select_related("destination")
            # latitude/longitude are nullable on Hotel — float(None) would crash
            # the serializer (same class of bug as DEF-022).
            ht_qs = ht_qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            if _name_query:
                ht_qs = ht_qs.filter(_match("name", "address", "destination__city"))
            ht_qs = _in_radius(ht_qs)
            for ht in ht_qs[:40]:
                raw_results.append({
                    "id": f"ht-{ht.id}",
                    "name": ht.name,
                    "category": "Hotel & Lodge",
                    "latitude": float(ht.latitude),
                    "longitude": float(ht.longitude),
                    "address": ht.address or (ht.destination.city if ht.destination else "Nepal"),
                    "city": ht.destination.city if ht.destination else "Pokhara",
                    "phone": ht.phone or "",
                    "source": "verified_hotel",
                    "is_destination": False,
                    "is_approximate": bool(getattr(ht, "is_approximate_coordinate", False)),
                })

        # DEF-022: the Restaurant table was documented as searched but never
        # actually queried — category=restaurant skipped this section entirely.
        if not cat_filter or cat_filter == "restaurant":
            rt_qs = Restaurant.objects.filter(status=Restaurant.Status.PUBLISHED)
            rt_qs = rt_qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            if _name_query:
                rt_qs = rt_qs.filter(_match("name", "address"))
            rt_qs = _in_radius(rt_qs)
            for rt in rt_qs[:40]:
                raw_results.append({
                    "id": f"rt-{rt.id}",
                    "name": rt.name,
                    "category": "Restaurant",
                    "latitude": float(rt.latitude),
                    "longitude": float(rt.longitude),
                    "address": rt.address or "Nepal",
                    "city": (rt.address.split(",")[-1].strip() if rt.address else ""),
                    "phone": rt.phone or "",
                    "source": "verified_restaurant",
                    "is_destination": False,
                })

        # 5. Search Nepal Landmarks & Administrative Boundaries
        from django.utils.text import slugify
        for k, v in NEPAL_LANDMARKS.items():
            if not cat_filter and (k in q or search_term in k):
                raw_results.append({
                    "id": f"landmark-{k.replace(' ', '-')}",
                    "name": v["name"],
                    "category": "Nepal Landmark",
                    "type": "landmark",
                    "slug": slugify(v["name"]),
                    "latitude": v["lat"],
                    "longitude": v["lng"],
                    "address": f"{v['city']}, {v['province']}",
                    "city": v["city"],
                    "source": "nepal_landmark",
                    "is_destination": True,
                })

        for muni_key, m_data in MUNICIPALITY_COORDINATES.items():
            if not cat_filter and (muni_key in q or search_term in muni_key):
                raw_results.append({
                    "id": f"muni-{muni_key}",
                    "name": muni_key.title(),
                    "category": "Administrative Hub",
                    "type": "administrative",
                    "slug": slugify(muni_key),
                    "latitude": m_data["lat"],
                    "longitude": m_data["lng"],
                    "address": f"{m_data['district']}, {m_data['province']}",
                    "city": m_data["district"],
                    "source": "administrative_boundary",
                    "is_destination": True,
                })

        # Calculate distances, bearings & directions
        processed = []
        seen = set()

        for row in raw_results:
            lat = row["latitude"]
            lng = row["longitude"]
            norm_key = f"{row['name'].lower()[:20]}_{round(lat, 3)}_{round(lng, 3)}"
            if norm_key in seen:
                continue
            seen.add(norm_key)

            dist_km = round(haversine_distance_km(ref_lat, ref_lng, lat, lng), 2)
            deg, comp, arrow = compute_bearing(ref_lat, ref_lng, lat, lng)

            row["distance_km"] = dist_km
            row["bearing_degrees"] = deg
            row["direction"] = comp
            row["compass_text"] = f"{comp} {arrow}"
            # Under a kilometre, metres read far better than "0.45 km" — the
            # 500 m radius searches are exactly where this matters most.
            row["distance_text"] = (
                "0 m (Here)" if dist_km < 0.005
                else f"{int(round(dist_km * 1000))} m" if dist_km < 1
                else f"{dist_km} km"
            )
            # Area-point coordinates must never be presented as a precise
            # distance: label them honestly (the UI already renders
            # `distance_label` ahead of its own fallbacks).
            if row.get("is_approximate"):
                row["distance_label"] = f"≈ {dist_km} km (area point)"
            processed.append(row)

        # Honour the requested radius — but ONLY when the user actually
        # provided GPS. Without GPS the reference point defaults to Pokhara,
        # and filtering by distance from an assumed location silently deleted
        # every text-search hit outside Pokhara (live bug: searching
        # "Swayambhunath" or "Thamel" with no GPS returned 0 results even
        # though both are published records). Nearby/category queries always
        # pass lat/lng, so they keep their radius behaviour.
        if radius_km and has_gps:
            processed = [row for row in processed if row["distance_km"] <= radius_km]

        # Ranking: when the user typed a substantive name (>= 6 chars), exact
        # and prefix name matches must outrank mere distance — otherwise
        # "Bandipur Eco Hotel" returns whatever lodge sits closest to the
        # reference point and "Bandipur" lists "Mountain Ridge Bandipur"
        # above Bandipur itself (live bug found 2026-09-21 consolidation
        # round). Short/generic queries ("bank", "hotels near me") keep the
        # pure nearest-first behaviour.
        _norm_term = re.sub(r"[^a-z0-9]", "", search_term)
        name_ranking = len(_norm_term) >= 6

        def _rank(item):
            if not name_ranking:
                return (0, 0, item["distance_km"])
            nm = re.sub(r"[^a-z0-9]", "", str(item.get("name", "")).lower())
            if nm == _norm_term:
                exact = 0
            elif nm.startswith(_norm_term):
                exact = 1
            else:
                exact = 2
            contains = 0 if _norm_term and _norm_term in nm else 1
            return (exact, contains, item["distance_km"])

        processed.sort(key=_rank)

        return processed[:limit]

    @staticmethod
    def merge_live_osm(results, ref_lat, ref_lng, radius_km, category="", limit=30):
        """Append OpenStreetMap points that are NOT in our database to an
        already-ranked nearby list (see ``_live_osm_nearby``).

        Only meaningful for a pure "near me" query — Overpass matches on
        location, not on names — so callers with a text query skip this. The
        merged list is distance-ranked (which is what a text-less nearby
        search already is) and truncated to ``limit``.

        Returns ``results`` untouched whenever live data is unavailable, so a
        provider outage can never cost the user their recorded rows.
        """
        try:
            live = _live_osm_nearby(ref_lat, ref_lng, radius_km, category)
        except Exception:
            return results
        if not live:
            return results
        try:
            radius_km = float(radius_km)
        except (TypeError, ValueError):
            return results

        combined = list(results)
        seen = {
            f"{str(r.get('name', '')).lower()[:20]}_{round(float(r.get('latitude') or 0), 3)}_"
            f"{round(float(r.get('longitude') or 0), 3)}"
            for r in combined
        }
        for row in live:
            key = (
                f"{row['name'].lower()[:20]}_{round(row['latitude'], 3)}_"
                f"{round(row['longitude'], 3)}"
            )
            if key in seen:
                continue
            dist_km = round(haversine_distance_km(ref_lat, ref_lng, row["latitude"], row["longitude"]), 2)
            if dist_km > radius_km:
                continue
            seen.add(key)
            deg, comp, arrow = compute_bearing(ref_lat, ref_lng, row["latitude"], row["longitude"])
            row["distance_km"] = dist_km
            row["bearing_degrees"] = deg
            row["direction"] = comp
            row["compass_text"] = f"{comp} {arrow}"
            row["distance_text"] = (
                "0 m (Here)" if dist_km < 0.005
                else f"{int(round(dist_km * 1000))} m" if dist_km < 1
                else f"{dist_km} km"
            )
            combined.append(row)

        combined.sort(key=lambda r: r.get("distance_km", 0))
        return combined[:limit]

    @staticmethod
    def resolve_single_place(query_or_name):
        """
        Resolves free-text query (e.g. "Lakeside", "Thamel", "Pashupatinath", "nearest bank")
        into a single normalized place object with valid coordinates.
        """
        if not query_or_name:
            return None

        q = str(query_or_name).strip().lower()

        # Check exact landmark
        if q in NEPAL_LANDMARKS:
            v = NEPAL_LANDMARKS[q]
            return {
                "name": v["name"], "latitude": v["lat"], "longitude": v["lng"],
                "city": v["city"], "address": f"{v['city']}, Nepal", "is_destination": True,
            }

        # Check municipality index before fuzzy destination matches, so
        # "Kathmandu" resolves to the city centre rather than whichever
        # destination row happens to mention Kathmandu.
        for suffix in ("", " municipality", " metropolitan city", " rural municipality"):
            entry = MUNICIPALITY_COORDINATES.get(f"{q}{suffix}")
            if entry:
                return {
                    "name": f"{q.title()}{suffix.title()}" if suffix else q.title(),
                    "latitude": entry["lat"],
                    "longitude": entry["lng"],
                    "city": q.title(),
                    "address": f"{entry.get('district', '')}, {entry.get('province', '')}, Nepal".strip(", "),
                    "is_destination": False,
                }

        # Check Destination table — exact and prefix matches take priority over
        # substring matches, so "Beni" resolves to Beni, not "Kagbeni Muktinath
        # Route" (live bug: icontains .first() returned arbitrary substring hits).
        from tourist.models import Destination
        _coord_qs = (Destination.objects.filter(is_active=True)
                     .exclude(latitude__isnull=True).exclude(longitude__isnull=True))
        dest = (
            _coord_qs.filter(name__iexact=q).first()
            or _coord_qs.filter(name__istartswith=q).first()
            or _coord_qs.filter(
                Q(name__icontains=q) | Q(slug__icontains=q) | Q(city__icontains=q)
            ).first()
        )

        if dest is None and len(q) >= 5:
            # Alias tier: consolidated rows carry former/duplicate names in
            # `aliases` (e.g. "Harion" -> Hariwan). Length-gated to avoid
            # stray substring hits.
            dest = (_coord_qs.filter(aliases__iexact=q).first()
                    or _coord_qs.filter(aliases__icontains=q).first())

        if dest is None:
            # Retry with query variants: strip a trailing locality token
            # ("Mahendra Cave Pokhara") and/or transliterate Nepali generic
            # words ("Mahendra Gufa" -> "Mahendra Cave"). Exact/prefix only —
            # never a fuzzy DB hit on a variant.
            toks = q.split()
            variants = []
            if len(toks) > 1 and toks[-1] in LOCALITY_SUFFIX_WORDS:
                variants.append(" ".join(toks[:-1]))
            translit = [NEPALI_TO_ENGLISH_WORDS.get(t, t) for t in toks]
            if translit != toks:
                variants.append(" ".join(translit))
                if len(translit) > 1 and translit[-1] in LOCALITY_SUFFIX_WORDS:
                    variants.append(" ".join(translit[:-1]))
            for variant in variants:
                if not variant or variant == q:
                    continue
                dest = (_coord_qs.filter(name__iexact=variant).first()
                        or _coord_qs.filter(name__istartswith=variant).first())
                if dest:
                    break

        if dest:
            return {
                "destination_id": dest.id,
                "name": dest.name,
                "slug": dest.slug,
                "latitude": float(dest.latitude),
                "longitude": float(dest.longitude),
                "city": dest.city or "Pokhara",
                "address": f"{dest.city or ''}, {dest.district or 'Nepal'}".strip(", "),
                "is_destination": True,
            }

        # Check places search — rank candidates by name similarity to the
        # query, so "Halesi Cave" resolves to Halesi Mahadev Cave rather than
        # the Kathmandu "Khotanghalesi guest house" that also contains the
        # substring (live bug). Destinations win ties over services.
        results = LocationSearchService.search_places(query=q, limit=30)
        min_score = 0.0
        if not results:
            # Typo-tolerant retry: strip generic place words so the searcher
            # sees a stem ("amhendra cave" -> "amhendra") and the similarity
            # ranker can still pick the true place — but only accept a strong
            # match (floor 0.75), otherwise stay honestly not-found.
            _generic = re.sub(
                r"\b(bazaar|bazar|temple|mandir|monastery|gompa|lake|pokhari|"
                r"pond|river|waterfall|jharana|jharna|falls|hills|hill|danda|"
                r"daha|cave|gufa|stupa|durbar|palace|park|viewpoint|base camp|"
                r"trek|dham|deurali|himal)\b", " ", q)
            _generic = re.sub(r"\s+", " ", _generic).strip()
            if _generic and _generic != q:
                results = LocationSearchService.search_places(query=_generic, limit=30)
                min_score = 0.75
        if results:
            import difflib as _difflib
            q_compact = re.sub(r"[^a-z0-9]", "", q)
            # core name with generic geographic words removed ("Bandipur
            # Bazaar" -> "bandipur"): a candidate named exactly/prefixed by
            # the core must beat fuzzy substring hits like "Bandipur
            # Mountain Resort".
            q_core = re.sub(
                r"\b(bazaar|bazar|temple|mandir|monastery|gompa|lake|pokhari|"
                r"pond|river|waterfall|jharana|jharna|falls|hills|hill|danda|"
                r"daha|cave|gufa|stupa|durbar|palace|park|viewpoint|base camp|"
                r"trek|dham|deurali|himal)\b", "", q)
            q_core = re.sub(r"[^a-z0-9]", "", q_core)

            def _rank(r):
                nm = re.sub(r"[^a-z0-9]", "", str(r.get("name", "")).lower())
                if q_core and (nm == q_core or (len(nm) >= 4 and q_core.startswith(nm))):
                    score = 2.0  # exact core-name match beats prefix matches
                elif q_core and nm.startswith(q_core):
                    score = 1.0
                else:
                    score = round(_difflib.SequenceMatcher(None, nm, q_compact).ratio(), 3)
                return (score, bool(r.get("is_destination")))

            item = max(results, key=_rank)
            if min_score and _rank(item)[0] < min_score:
                return None  # stem retry found no strong match — honest not-found
            return {
                "name": item["name"],
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "city": item.get("city", "Pokhara"),
                "address": item.get("address", "Nepal"),
                "is_destination": item.get("is_destination", True),
            }

        # Last-resort typo tolerance: fuzzy-compare the query against
        # destination names directly ("amhendra cave" ~ "Mahendra Cave").
        # Strict floor (0.85 ≈ ≥90% of characters aligned) so misspellings
        # resolve but unrelated text stays honestly not-found.
        if len(q_compact := re.sub(r"[^a-z0-9]", "", q)) >= 6:
            import difflib as _difflib
            best_row, best_ratio = None, 0.0
            qs = (Destination.objects.filter(is_active=True)
                  .exclude(latitude__isnull=True).exclude(longitude__isnull=True))
            for row in qs.values("id", "name", "slug", "city", "district",
                                 "latitude", "longitude").iterator():
                nm = re.sub(r"[^a-z0-9]", "", str(row["name"]).lower())
                if not nm or abs(len(nm) - len(q_compact)) > max(4, len(q_compact) // 3):
                    continue  # cheap length pre-filter
                ratio = _difflib.SequenceMatcher(None, nm, q_compact).ratio()
                if ratio > best_ratio:
                    best_row, best_ratio = row, ratio
            if best_row and best_ratio >= 0.85:
                return {
                    "destination_id": best_row["id"],
                    "name": best_row["name"],
                    "slug": best_row["slug"],
                    "latitude": float(best_row["latitude"]),
                    "longitude": float(best_row["longitude"]),
                    "city": best_row["city"] or "Pokhara",
                    "address": f"{best_row['city'] or ''}, {best_row['district'] or 'Nepal'}".strip(", "),
                    "is_destination": True,
                }

        # No fabricated fallback: an unrecognized place resolves to None so
        # callers surface "not found" instead of silently routing from/to
        # Pokhara. (Golden rule: never present invented coordinates as fact.)
        return None
