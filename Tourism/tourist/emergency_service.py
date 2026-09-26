"""Location-aware emergency directory built from the SQLite source of truth."""
from django.db.models import Q

from .models import Destination, EmergencyContact, Hospital, OSMEssentialService, PoliceStation
from .utils import bounding_box, haversine_distance

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
        return fallback, bool(fallback)
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


def _ranked_nearby(rows, latitude, longitude, radius_km, minimum=1):
    """(distance, row) pairs sorted by straight-line distance.

    A SQL bounding box narrows the scan to rows around the point (hundreds
    of rows instead of every hospital/police station/bank in Nepal on every
    request). Only when the box holds fewer than ``minimum`` rows — a remote
    location — does it fall back to the full table so the nearest facilities
    can still be listed and flagged as outside the requested radius.
    """
    box = bounding_box(latitude, longitude, radius_km)
    boxed = rows.filter(
        latitude__gte=box["min_lat"], latitude__lte=box["max_lat"],
        longitude__gte=box["min_lon"], longitude__lte=box["max_lon"],
    )
    candidates = list(boxed)
    if len(candidates) < minimum:
        candidates = list(rows)
    ranked = [
        (haversine_distance(latitude, longitude, float(row.latitude), float(row.longitude)), row)
        for row in candidates
        if row.latitude is not None and row.longitude is not None
    ]
    ranked.sort(key=lambda pair: pair[0])
    return ranked


def _nearest_rows(rows, latitude, longitude, limit, radius_km, mapper):
    ranked = _ranked_nearby(rows, latitude, longitude, radius_km, minimum=limit)
    within = [pair for pair in ranked if pair[0] <= radius_km]
    chosen = (within or ranked)[:limit]
    items = [mapper(row, round(distance, 2), distance > radius_km) for distance, row in chosen]
    for item in items:
        item["estimated_travel_time_min"] = max(1, round(item["distance_km"] / 30 * 60))
        item["travel_time_basis"] = "Rough estimate: straight-line distance at 30 km/h — not a road route"
    return items


def build_emergency_directory(latitude, longitude, destination=None, radius_km=50, limit=8):
    latitude, longitude = float(latitude), float(longitude)

    def _image_url(row):
        try:
            return row.image.url if row.image else None
        except (ValueError, AttributeError):
            return None

    def hospital_item(row, distance, outside_radius):
        phone, _ = clean_phone(row.phone, "")
        return {
            "id": f"hospital-{row.id}", "type": "hospital", "name": row.name,
            "address": row.address, "district": row.district,
            "phone_number": phone, "phone_is_national_fallback": False,
            "latitude": float(row.latitude), "longitude": float(row.longitude),
            "distance_km": distance, "outside_requested_radius": outside_radius,
            "image_url": _image_url(row),
            "opening_hours": row.opening_hours, "emergency_available": row.emergency_available,
            "verified": row.is_verified, "verified_at": row.verified_at, "updated_at": row.updated_at,
            "source_name": row.source_name or "",
            "source_url": row.source_url or "",
        }

    def police_item(row, distance, outside_radius):
        phone, _ = clean_phone(row.phone, "")
        return {
            "id": f"police-{row.id}", "type": "police", "name": row.name,
            "address": row.address, "district": destination.district if destination else "",
            "phone_number": phone, "phone_is_national_fallback": False,
            "latitude": float(row.latitude), "longitude": float(row.longitude),
            "distance_km": distance, "outside_requested_radius": outside_radius,
            "image_url": _image_url(row),
            "opening_hours": row.opening_hours, "emergency_available": row.emergency_available,
            "verified": row.is_verified, "verified_at": row.verified_at, "updated_at": row.updated_at,
            "source_name": row.source_name or "",
            "source_url": row.source_url or "",
        }

    hospitals = _nearest_rows(
        Hospital.objects.filter(is_archived=False), latitude, longitude, limit, radius_km, hospital_item,
    )
    police = _nearest_rows(
        PoliceStation.objects.filter(is_archived=False), latitude, longitude, limit, radius_km, police_item,
    )

    local_contacts = []
    contacts = EmergencyContact.objects.exclude(phone_number__in=["", None])
    for contact in contacts:
        distance = haversine_distance(latitude, longitude, float(contact.latitude), float(contact.longitude))
        local_contacts.append((distance, contact))
    local_contacts.sort(key=lambda pair: pair[0])
    specialized = []
    for distance, contact in local_contacts:
        if len(specialized) >= limit:
            break
        contact_phone, _ = clean_phone(contact.phone_number, "")
        specialized.append({
            "id": f"contact-{contact.id}", "type": contact.contact_type,
            "name": contact.name, "address": contact.address, "district": contact.city,
            "phone_number": contact_phone,
            "alternate_phone": str(contact.alternate_phone or ""),
            "latitude": float(contact.latitude), "longitude": float(contact.longitude),
            "distance_km": round(distance, 2), "outside_requested_radius": distance > radius_km,
            "estimated_travel_time_min": max(1, round(distance / 30 * 60)),
            "travel_time_basis": "Rough estimate: straight-line distance at 30 km/h — not a road route",
            "is_24_hours": contact.is_24_hours, "source_name": "Verified emergency directory", "source_url": "",
        })

    # Admin-approved and OpenStreetMap fire, ambulance, bank, pharmacy and
    # tourism-office records share the same accurate distance calculation.
    existing_ids = {item["id"] for item in specialized}
    osm_ranked = _ranked_nearby(
        OSMEssentialService.objects.filter(is_archived=False).exclude(category__in=["hospital", "police"]),
        latitude, longitude, radius_km, minimum=limit,
    )
    # Cap per category, not overall: banks and ATMs outnumber pharmacies
    # roughly 3:1, so a single "nearest 24" cap filled up with banks and the
    # pharmacy count near Pokhara was always 0 despite 351 pharmacy rows.
    per_category = {}
    for distance, service in osm_ranked:
        category = "atm_bank" if service.category in {"atm", "bank"} else service.category
        if per_category.get(category, 0) >= limit:
            continue
        item_id = f"essential-{service.id}"
        if item_id in existing_ids:
            continue
        per_category[category] = per_category.get(category, 0) + 1
        specialized.append({
            "id": item_id, "type": service.category, "name": service.name,
            "address": service.address, "district": service.raw_tags.get("district", ""),
            "phone_number": service.phone, "alternate_phone": "",
            "latitude": float(service.latitude), "longitude": float(service.longitude),
            "distance_km": round(distance, 2), "outside_requested_radius": distance > radius_km,
            "estimated_travel_time_min": max(1, round(distance / 30 * 60)),
            "travel_time_basis": "Rough estimate: straight-line distance at 30 km/h — not a road route",
            "is_24_hours": service.emergency_available,
            "opening_hours": service.opening_hours,
            "image_url": _image_url(service),
            "verified": service.is_verified, "verified_at": service.verified_at, "updated_at": service.updated_at,
            "source_name": service.source_name or "",
            "source_url": service.source_url or "",
        })

    facility_counts = {
        "hospitals_within_radius": sum(1 for item in hospitals if not item["outside_requested_radius"]),
        "police_within_radius": sum(1 for item in police if not item["outside_requested_radius"]),
        "specialized_contacts_within_radius": sum(1 for item in specialized if not item["outside_requested_radius"]),
        "pharmacy_within_radius": sum(1 for item in specialized if item["type"] == "pharmacy" and not item["outside_requested_radius"]),
        "atm_bank_within_radius": sum(1 for item in specialized if item["type"] in {"atm", "bank"} and not item["outside_requested_radius"]),
        "fire_within_radius": sum(1 for item in specialized if item["type"] == "fire_station" and not item["outside_requested_radius"]),
        "database_hospitals": Hospital.objects.filter(is_archived=False).count(),
        "database_police_stations": PoliceStation.objects.filter(is_archived=False).count(),
    }
    coverage_gap = (
        facility_counts["hospitals_within_radius"] == 0
        and facility_counts["police_within_radius"] == 0
    )
    place_label = destination.name if destination else "this location"
    notice = (
        "Results are distance-ranked from stored coordinates. A national hotline is shown when a local dataset phone is unavailable. Confirm local availability when safe to do so."
    )
    if coverage_gap:
        notice += (
            f" There is no verified local hospital or police record near {place_label} in this directory. "
            "National hotlines still work. An administrator can add an accurate hospital, police station, pharmacy or fire station with coordinates, "
            "or you can submit a facility for review at /submit-service."
        )
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
        "coverage_gap": coverage_gap,
        "notice": notice,
    }
