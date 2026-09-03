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

        # Detect category intents (e.g. "bank", "atm", "hospital", "pharmacy", "police", "store")
        cat_filter = (category or "").strip().lower()
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

        raw_results = []

        # 1. Search Destination model
        from tourist.models import (
            Destination, Hotel, Restaurant, Hospital, PoliceStation,
            OSMEssentialService, OSMTourismPlace
        )

        dest_qs = Destination.objects.filter(is_active=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        if search_term and not cat_filter:
            dest_qs = dest_qs.filter(
                Q(name__icontains=search_term) | Q(city__icontains=search_term) |
                Q(district__icontains=search_term) | Q(slug__icontains=search_term)
            )

        for d in dest_qs[:30]:
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
                "image_url": d.cover_image or "",
                "source": "verified_database",
                "is_destination": True,
            })

        # 2. Search OSMEssentialService (Banks, ATMs, Pharmacies, Stores, Gas Stations, etc.)
        osm_qs = OSMEssentialService.objects.exclude(is_archived=True)
        if cat_filter:
            osm_qs = osm_qs.filter(category__icontains=cat_filter)
        elif search_term:
            osm_qs = osm_qs.filter(Q(name__icontains=search_term) | Q(address__icontains=search_term) | Q(category__icontains=search_term))

        for s in osm_qs[:40]:
            raw_results.append({
                "id": f"osm-{s.id}",
                "name": s.name,
                "category": s.category.replace("_", " ").title(),
                "latitude": float(s.latitude),
                "longitude": float(s.longitude),
                "address": s.address or f"{s.district or 'Nepal'}",
                "city": s.district or "Pokhara",
                "phone": s.phone or "",
                "image_url": s.image.url if getattr(s, "image", None) else "",
                "source": "osm_essential_service",
                "is_destination": False,
            })

        # 3. Search Hospitals & Police Stations
        if not cat_filter or cat_filter == "hospital":
            h_qs = Hospital.objects.all()
            if search_term and cat_filter != "hospital":
                h_qs = h_qs.filter(Q(name__icontains=search_term) | Q(address__icontains=search_term))
            for h in h_qs[:20]:
                raw_results.append({
                    "id": f"hosp-{h.id}",
                    "name": h.name,
                    "category": "Hospital",
                    "latitude": float(h.latitude),
                    "longitude": float(h.longitude),
                    "address": h.address or "Nepal",
                    "city": h.destination.city if getattr(h, "destination", None) else "Pokhara",
                    "phone": h.phone or "102",
                    "source": "verified_hospital",
                    "is_destination": False,
                })

        if not cat_filter or cat_filter == "police":
            p_qs = PoliceStation.objects.all()
            if search_term and cat_filter != "police":
                p_qs = p_qs.filter(Q(name__icontains=search_term) | Q(address__icontains=search_term))
            for p in p_qs[:20]:
                raw_results.append({
                    "id": f"pol-{p.id}",
                    "name": p.name,
                    "category": "Police Station",
                    "latitude": float(p.latitude),
                    "longitude": float(p.longitude),
                    "address": p.address or "Nepal",
                    "city": p.destination.city if getattr(p, "destination", None) else "Pokhara",
                    "phone": p.phone or "100",
                    "source": "verified_police",
                    "is_destination": False,
                })

        # 4. Search Hotels & Restaurants
        if not cat_filter or cat_filter == "hotel":
            ht_qs = Hotel.objects.filter(is_active=True).select_related("destination")
            if search_term and cat_filter != "hotel":
                ht_qs = ht_qs.filter(Q(name__icontains=search_term) | Q(address__icontains=search_term) | Q(destination__city__icontains=search_term))
            for ht in ht_qs[:20]:
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
            row["distance_text"] = "0 km (Here)" if dist_km < 0.1 else f"{dist_km} km"
            processed.append(row)

        # Sort nearest first if user provided GPS or category filter was selected
        if has_gps or cat_filter:
            processed.sort(key=lambda item: item["distance_km"])
        else:
            # Sort exact keyword matches first, then distance
            def _rank(item):
                name_match = 0 if search_term in item["name"].lower() else 1
                return (name_match, item["distance_km"])
            processed.sort(key=_rank)

        return processed[:limit]

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

        # Check Destination table
        from tourist.models import Destination
        dest = Destination.objects.filter(
            Q(name__icontains=q) | Q(slug__icontains=q) | Q(city__icontains=q),
            is_active=True
        ).exclude(latitude__isnull=True).exclude(longitude__isnull=True).first()

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

        # Check places search
        results = LocationSearchService.search_places(query=q, limit=1)
        if results:
            item = results[0]
            return {
                "name": item["name"],
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "city": item.get("city", "Pokhara"),
                "address": item.get("address", "Nepal"),
                "is_destination": item.get("is_destination", True),
            }

        # Fallback to Pokhara center
        return {
            "name": query_or_name.title(),
            "latitude": POKHARA_CENTER[0],
            "longitude": POKHARA_CENTER[1],
            "city": "Pokhara",
            "address": "Pokhara, Gandaki Province, Nepal",
            "is_destination": True,
        }
