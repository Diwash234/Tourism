"""Location-aware emergency directory built from the SQLite source of truth."""
from django.db.models import Q

from .models import Destination, EmergencyContact, Hospital, OSMEssentialService, PoliceStation
from .utils import haversine_distance

NATIONAL_HOTLINES = [
    {"type": "tourist_police", "name": "Tourist Police Nepal", "phone_number": "1144", "alternate_phone": "+977-1-4247041", "description": "Toll-free tourist assistance across Nepal", "source_name": "Nepal Police / Nepal Tourism Board", "source_url": "https://cid.nepalpolice.gov.np/cid-wings/tourist-police/"},
    {"type": "police", "name": "Nepal Police Control", "phone_number": "100", "alternate_phone": "16600141516", "description": "National police emergency dispatch", "source_name": "Nepal Police", "source_url": "https://npsc.nepalpolice.gov.np/contact-us/"},
    {"type": "ambulance", "name": "National Ambulance", "phone_number": "102", "alternate_phone": "", "description": "National medical emergency line", "source_name": "Nepal emergency short code", "source_url": "https://heoc.mohp.gov.np/"},
    {"type": "fire_station", "name": "Fire Brigade", "phone_number": "101", "alternate_phone": "", "description": "National fire emergency line", "source_name": "Nepal emergency short code", "source_url": "https://mohp.gov.np/"},
    {"type": "traffic_police", "name": "Traffic Police", "phone_number": "103", "alternate_phone": "", "description": "Road accidents, closures and traffic assistance", "source_name": "Nepal Police", "source_url": "https://cid.nepalpolice.gov.np/cid-wings/tourist-police/"},
]


def clean_phone(value, fallback):
    value = str(value or "").strip()
    if not value or value.lower() in {"nan", "none", "null"}:
        return fallback, True
    if value.endswith(".0"):
        value = value[:-2]
    value = value.replace(" ", "")
    if value.startswith("9770"):
        value = "+977" + value[4:]
    elif value.startswith("977"):
        value = "+" + value
    return value, False


def resolve_destination(reference):
    ref = str(reference or "").strip()
    if not ref:
        return None
    query = Q(slug__iexact=ref) | Q(name__iexact=ref)
    if ref.isdigit():
        query |= Q(pk=int(ref))
    base = Destination.objects.filter(
        is_active=True, status=Destination.SubmissionStatus.APPROVED
    )
    destination = base.filter(query).first()
    if destination:
        return destination
    return base.filter(
        Q(name__icontains=ref) | Q(city__icontains=ref) |
        Q(district__icontains=ref) | Q(municipality__icontains=ref)
    ).order_by("-average_rating", "name").first()


def _nearest_rows(rows, latitude, longitude, limit, radius_km, mapper):
    ranked = []
    for row in rows:
        distance = haversine_distance(latitude, longitude, float(row.latitude), float(row.longitude))
        ranked.append((distance, row))
    ranked.sort(key=lambda pair: pair[0])
    within = [pair for pair in ranked if pair[0] <= radius_km]
    chosen = (within or ranked)[:limit]
    return [mapper(row, round(distance, 2), distance > radius_km) for distance, row in chosen]


def build_emergency_directory(latitude, longitude, destination=None, radius_km=50, limit=8):
    latitude, longitude = float(latitude), float(longitude)

    def hospital_item(row, distance, outside_radius):
        phone, fallback = clean_phone(row.phone, "102")
        return {
            "id": f"hospital-{row.id}", "type": "hospital", "name": row.name,
            "address": row.address, "district": row.district,
            "phone_number": phone, "phone_is_national_fallback": fallback,
            "latitude": float(row.latitude), "longitude": float(row.longitude),
            "distance_km": distance, "outside_requested_radius": outside_radius,
            "image_url": row.image.url if row.image else None,
            "source_name": "Nepal hospital dataset", "source_url": "https://mohp.gov.np/",
        }

    def police_item(row, distance, outside_radius):
        phone, fallback = clean_phone(row.phone, "100")
        return {
            "id": f"police-{row.id}", "type": "police", "name": row.name,
            "address": row.address, "district": destination.district if destination else "",
            "phone_number": phone, "phone_is_national_fallback": fallback,
            "latitude": float(row.latitude), "longitude": float(row.longitude),
            "distance_km": distance, "outside_requested_radius": outside_radius,
            "image_url": row.image.url if row.image else None,
            "source_name": "Nepal police station dataset", "source_url": "https://nepalpolice.gov.np/",
        }

    hospitals = _nearest_rows(Hospital.objects.all(), latitude, longitude, limit, radius_km, hospital_item)
    police = _nearest_rows(PoliceStation.objects.all(), latitude, longitude, limit, radius_km, police_item)

    local_contacts = []
    contacts = EmergencyContact.objects.all()
    for contact in contacts:
        distance = haversine_distance(latitude, longitude, float(contact.latitude), float(contact.longitude))
        local_contacts.append((distance, contact))
    local_contacts.sort(key=lambda pair: pair[0])
    specialized = []
    for distance, contact in local_contacts:
        if len(specialized) >= limit:
            break
        specialized.append({
            "id": f"contact-{contact.id}", "type": contact.contact_type,
            "name": contact.name, "address": contact.address, "district": contact.city,
            "phone_number": str(contact.phone_number),
            "alternate_phone": str(contact.alternate_phone or ""),
            "latitude": float(contact.latitude), "longitude": float(contact.longitude),
            "distance_km": round(distance, 2), "outside_requested_radius": distance > radius_km,
            "is_24_hours": contact.is_24_hours, "source_name": "Verified emergency directory", "source_url": "",
        })

    # Admin-approved and OpenStreetMap fire, ambulance, bank, pharmacy and
    # tourism-office records share the same accurate distance calculation.
    existing_ids = {item["id"] for item in specialized}
    osm_ranked = []
    for service in OSMEssentialService.objects.exclude(category__in=["hospital", "police"]):
        distance = haversine_distance(latitude, longitude, float(service.latitude), float(service.longitude))
        osm_ranked.append((distance, service))
    osm_ranked.sort(key=lambda pair: pair[0])
    for distance, service in osm_ranked:
        if len(specialized) >= limit:
            break
        item_id = f"essential-{service.id}"
        if item_id in existing_ids:
            continue
        specialized.append({
            "id": item_id, "type": service.category, "name": service.name,
            "address": service.address, "district": service.raw_tags.get("district", ""),
            "phone_number": service.phone, "alternate_phone": "",
            "latitude": float(service.latitude), "longitude": float(service.longitude),
            "distance_km": round(distance, 2), "outside_requested_radius": distance > radius_km,
            "is_24_hours": False,
            "image_url": service.image.url if service.image else None,
            "source_name": "Admin verified" if service.osm_id.startswith("community/") else "OpenStreetMap",
            "source_url": "https://www.openstreetmap.org/" if not service.osm_id.startswith("community/") else "",
        })

    facility_counts = {
        "hospitals_within_radius": sum(1 for item in hospitals if not item["outside_requested_radius"]),
        "police_within_radius": sum(1 for item in police if not item["outside_requested_radius"]),
        "specialized_contacts_within_radius": sum(1 for item in specialized if not item["outside_requested_radius"]),
        "database_hospitals": Hospital.objects.count(),
        "database_police_stations": PoliceStation.objects.count(),
    }
    location = {
        "latitude": latitude, "longitude": longitude,
        "source": "destination" if destination else "coordinates",
    }
    if destination:
        location.update({
            "destination_id": destination.id, "destination_name": destination.name,
            "destination_slug": destination.slug, "district": destination.district,
            "province": destination.province,
        })

    return {
        "location": location, "radius_km": radius_km, "counts": facility_counts,
        "hospitals": hospitals, "police": police, "specialized_contacts": specialized,
        "national_hotlines": NATIONAL_HOTLINES,
        "notice": "Results are distance-ranked from stored coordinates. A national hotline is shown when a local dataset phone is unavailable. Confirm local availability when safe to do so.",
    }
