"""Additive 200-city / 15-day itinerary planner.

Existing curated itineraries are never deleted or replaced. This planner resolves
factual places/services from the existing database at request time.
"""
from math import radians, sin, cos, asin, sqrt
from django.db.models import Q

_CITY_LINES = """
Bagmati|Kathmandu,Lalitpur,Bharatpur,Hetauda,Budhanilkantha,Tarakeshwar,Gokarneshwar,Suryabinayak,Chandragiri,Tokha,Kageshwari-Manohara,Mahalaxmi,Madhyapur Thimi,Nagarjun,Kirtipur,Bhaktapur,Kamalamai,Khairahani,Rapti,Dudhauli,Banepa,Bidur,Nilkantha,Panauti,Panchkhal,Dhulikhel,Manthali,Bhimeshwar,Jiri,Chautara,Melamchi,Dhunibeshi,Thaha,Madi,Kalika,Ratnanagar,Makwanpur,Namobuddha,Mandandeupur,Belkotgadhi
Koshi|Biratnagar,Itahari,Dharan,Mechinagar,Sundar Haraicha,Birtamod,Damak,Triyuga,Inaruwa,Shivasatakshi,Arjundhara,Belbari,Pathari-Shanishchare,Urlabari,Bhadrapur,Duhabi,Gauradaha,Kankai,Rangeli,Letang,Sunwarshi,Ramdhuni,Barahakshetra,Ratuwamai,Ilam,Suryodaya,Phidim,Dhankuta,Khandbari,Chainpur,Bhojpur,Katari
Madhesh|Birgunj,Janakpur,Kalaiya,Jitpursimara,Lahan,Rajbiraj,Bardibas,Ishwarpur,Lalbandi,Chandrapur,Barahathawa,Mirchaiya,Garuda,Gaur,Malangwa,Hariwan,Gaushala,Mahagadhimai,Kalyanpur,Dhangadhimai,Bhangaha,Surunga,Simraungadh,Godaita,Rajpur,Gadhimai,Shahidnagar,Hanumannagar Kankalini,Khadak,Dhanushadham,Mithila,Pokhariya
Lumbini|Ghorahi,Butwal,Tulsipur,Nepalgunj,Tilottama,Kohalpur,Banganga,Sainamaina,Siddharthanagar,Bardaghat,Gulariya,Krishnanagar,Buddhabhumi,Shivaraj,Devdaha,Sunawal,Tansen,Lamahi,Rajapur,Barbardiya,Madhuwan,Thakurbaba,Rampur,Sitganga,Resunga,Sandhikharka,Pyuthan,Swargadwari,Rolpa,Musikot,Banglachuli,Kapilvastu,Maharajgunj,Lumbini Sanskritik,Jaleshwar
Gandaki|Pokhara,Gaindakot,Vyas,Baglung,Waling,Shuklagandaki,Gorkha,Besisahar,Kushma,Palungtar,Putalibazar,Galyang,Bhirkot,Chapakot,Madhyabindu,Kawasoti,Devchuli,Beni,Rainas,Sundarbazar,Madhya Nepal,Bandipur,Bhimad,Jomsom,Bhanu
Karnali|Birendranagar,Diktel,Aathbiskot,Chaurjahari,Sharada,Bagchaur,Bheriganga,Gurbhakot,Panchapuri,Chhayanath Rara,Chandannath,Dullu,Aathabis,Bheri,Chhedagad,Nalgad,Jajarkot,Khandachakra
Sudurpashchim|Dhangadhi,Bhimdatta,Godawari,Tikapur,Ghodaghodi,Krishnapur,Shuklaphanta,Belauri,Bedkot,Punarbas,Lamki-Chuha,Gauriganga,Bhajani,Bardagoria,Dipayal Silgadhi,Dadeldhura,Amargadhi,Puchaudi
""".strip()

CITY_CATALOG = []
for line in _CITY_LINES.splitlines():
    province, names = line.split("|", 1)
    for name in names.split(","):
        CITY_CATALOG.append({"name": name.strip(), "province": province})
assert len(CITY_CATALOG) == 200
assert len({x["name"].casefold() for x in CITY_CATALOG}) == 200

DAY_THEMES = [
    ("Arrival & orientation", "arrival"),
    ("Signature heritage / landmark", "heritage"),
    ("Nature & viewpoints", "nature"),
    ("Culture, religion & history", "culture"),
    ("Local food & market", "food"),
    ("Nearby short excursion", "excursion"),
    ("Rest & weather buffer", "rest"),
    ("Outdoor / responsible adventure", "adventure"),
    ("Community / living culture", "community"),
    ("Second regional excursion", "excursion"),
    ("Photography & signature sights", "photo"),
    ("Shopping & local lifestyle", "lifestyle"),
    ("Contingency / weather day", "buffer"),
    ("Slow final sightseeing", "slow"),
    ("Departure / onward travel", "departure"),
]

def _distance(a_lat, a_lon, b_lat, b_lon):
    if None in (a_lat, a_lon, b_lat, b_lon):
        return None
    r = 6371.0088
    p1, p2 = radians(float(a_lat)), radians(float(b_lat))
    dp, dl = radians(float(b_lat)-float(a_lat)), radians(float(b_lon)-float(a_lon))
    h = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return round(2*r*asin(sqrt(h)), 2)

def _nearest(rows, lat, lon, limit=3):
    scored = []
    for row in rows:
        d = _distance(lat, lon, row.latitude, row.longitude)
        if d is not None:
            scored.append((d, row))
    scored.sort(key=lambda x: x[0])
    return scored[:limit]

def build_city_15_day(city, request=None):
    """Build a 15-day plan from real project records; never invent missing facts."""
    from .models import Destination, Hotel, Hospital, PoliceStation
    from .serializers import public_destination_cover

    target = next((x for x in CITY_CATALOG if x["name"].casefold() == city.strip().casefold()), None)
    if not target:
        return None

    name, province = target["name"], target["province"]
    q = Q(city__iexact=name) | Q(city__icontains=name) | Q(name__iexact=name)
    dests = list(Destination.publicly_visible().filter(q)
                 .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
                 .order_by("-average_rating", "-ratings_count", "name")[:80])

    aliases = {"Vyas": "Damauli", "Siddharthanagar": "Bhairahawa",
               "Bhimdatta": "Mahendranagar", "Besisahar": "Besishahar"}
    if not dests and name in aliases:
        a = aliases[name]
        dests = list(Destination.publicly_visible().filter(
            Q(city__icontains=a) | Q(name__icontains=a))
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            .order_by("-average_rating", "-ratings_count", "name")[:80])

    # Keep only unique real destinations.
    seen, unique = set(), []
    for d in dests:
        k = (d.name or "").strip().casefold()
        if k and k not in seen:
            seen.add(k); unique.append(d)

    if not unique:
        return {
            "city": name, "province": province, "days": 15, "nights": 14,
            "data_status": "needs_verified_destination_data",
            "data_quality": {"verified_destination_count": 0, "fabricated_facts": 0},
            "itinerary": [{"day": i, "title": f"Day {i} — {t}", "focus": f,
                           "destinations": [], "status": "needs_verified_destination_data"}
                          for i, (t, f) in enumerate(DAY_THEMES, 1)]
        }

    anchor = unique[0]
    hotel_rows = list(Hotel.objects.filter(is_active=True).filter(
        Q(city__icontains=name) | Q(name__icontains=name))
        .exclude(latitude__isnull=True).exclude(longitude__isnull=True)[:30])
    hospital_rows = list(Hospital.objects.filter(is_archived=False).filter(
        Q(city__icontains=name) | Q(name__icontains=name))
        .exclude(latitude__isnull=True).exclude(longitude__isnull=True)[:20])
    police_rows = list(PoliceStation.objects.filter(is_archived=False).filter(
        Q(city__icontains=name) | Q(name__icontains=name))
        .exclude(latitude__isnull=True).exclude(longitude__isnull=True)[:20])

    hotels = _nearest(hotel_rows, anchor.latitude, anchor.longitude)
    hospitals = _nearest(hospital_rows, anchor.latitude, anchor.longitude)
    police = _nearest(police_rows, anchor.latitude, anchor.longitude)

    def service(pair):
        d, row = pair
        out = {"id": row.id, "name": row.name, "distance_km": d,
               "is_verified": bool(getattr(row, "is_verified", False))}
        for field in ("phone", "website", "address", "source", "source_name"):
            value = getattr(row, field, None)
            if value:
                out[field] = str(value)
        return out

    service_data = {
        "hotels": [service(x) for x in hotels],
        "hospitals": [service(x) for x in hospitals],
        "police": [service(x) for x in police],
        "emergency_numbers": {"police": "100", "ambulance": "102"},
    }

    itinerary = []
    for day_no, (title, focus) in enumerate(DAY_THEMES, 1):
        picks = [] if focus in ("rest", "buffer", "departure") else unique[(day_no-1)*2:(day_no-1)*2+2]
        day_destinations = []
        legs = []
        previous = anchor
        for d in picks:
            day_destinations.append({
                "id": d.id, "name": d.name, "city": d.city or name,
                "district": d.district or "", "province": d.province or province,
                "latitude": float(d.latitude), "longitude": float(d.longitude),
                "elevation_m": d.elevation_m,
                "cover_image_url": public_destination_cover(d, request) if request else None,
                "short_description": d.short_description or d.description or "",
                "best_time_to_visit": d.best_time_to_visit or "",
                "source": d.source or "",
                "coordinate_source": d.coordinate_source or "",
                "coordinate_status": d.coordinate_status,
                "research_status": d.research_status,
            })
            dist = _distance(previous.latitude, previous.longitude, d.latitude, d.longitude)
            if dist is not None:
                legs.append({"from": previous.name, "to": d.name,
                             "distance_km": dist,
                             "distance_type": "straight_line_planning_estimate",
                             "routing_note": "Use the navigation/routing endpoint for road distance and travel time."})
            previous = d

        itinerary.append({
            "day": day_no, "title": f"Day {day_no} — {title}", "focus": focus,
            "city": name, "destinations": day_destinations, "legs": legs,
            "nearby_services": service_data,
            "overnight": {"hotel_options": service_data["hotels"]},
            "safety": {"hospitals": service_data["hospitals"],
                       "police": service_data["police"],
                       "emergency_numbers": service_data["emergency_numbers"]},
        })

    return {
        "city": name, "province": province, "days": 15, "nights": 14,
        "data_status": "database_resolved",
        "planning_method": "Pokhara sample structure + existing project data",
        "data_quality": {
            "destination_records": len(unique),
            "hotel_candidates": len(hotel_rows),
            "hospital_candidates": len(hospital_rows),
            "police_candidates": len(police_rows),
            "fabricated_facts": 0,
        },
        "city_anchor": {"destination_id": anchor.id, "name": anchor.name,
                        "latitude": float(anchor.latitude), "longitude": float(anchor.longitude),
                        "coordinate_status": anchor.coordinate_status},
        "itinerary": itinerary,
    }
