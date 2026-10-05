"""Location-aware emergency directory built from the SQLite source of truth."""
import time

from django.db.models import Count, Max, Q

from .models import Destination, EmergencyContact, Hospital, OSMEssentialService, PoliceStation, SiteSetting
from .phone_quality import is_placeholder_phone
from .utils import bounding_box, haversine_distance

NATIONAL_HOTLINES = [
    {"type": "tourist_police", "name": "Tourist Police Nepal", "phone_number": "1144", "alternate_phone": "+977-1-4247041", "description": "Toll-free tourist assistance across Nepal", "source_name": "Nepal Police / Nepal Tourism Board", "source_url": "https://cid.nepalpolice.gov.np/cid-wings/tourist-police/"},
    {"type": "police", "name": "Nepal Police Control", "phone_number": "100", "alternate_phone": "16600141516", "description": "National police emergency dispatch", "source_name": "Nepal Police", "source_url": "https://npsc.nepalpolice.gov.np/contact-us/"},
    {"type": "ambulance", "name": "National Ambulance", "phone_number": "102", "alternate_phone": "", "description": "National medical emergency line", "source_name": "Nepal emergency short code", "source_url": "https://heoc.mohp.gov.np/"},
    {"type": "fire_station", "name": "Fire Brigade", "phone_number": "101", "alternate_phone": "", "description": "National fire emergency line", "source_name": "Nepal emergency short code", "source_url": "https://mohp.gov.np/"},
    {"type": "traffic_police", "name": "Traffic Police", "phone_number": "103", "alternate_phone": "", "description": "Road accidents, closures and traffic assistance", "source_name": "Nepal Police", "source_url": "https://cid.nepalpolice.gov.np/cid-wings/tourist-police/"},
]


HOTLINE_SETTING_KEY = "national_emergency_hotlines"
# These five safety-critical national services must remain visible. An admin
# can edit their verified wording/source or add/remove non-critical entries,
# but the application will not allow a bad CMS value to make dispatch numbers
# disappear.
REQUIRED_HOTLINE_TYPES = {"tourist_police", "police", "ambulance", "fire_station", "traffic_police"}


def _hotline_row(value):
    if not isinstance(value, dict):
        return None
    hotline_type = str(value.get("type") or "").strip().lower()[:40]
    name = str(value.get("name") or "").strip()[:200]
    phone = str(value.get("phone_number") or "").strip()[:60]
    source_name = str(value.get("source_name") or "").strip()[:160]
    source_url = str(value.get("source_url") or "").strip()[:600]
    if not hotline_type or not name or not phone or not source_name:
        return None
    if source_url and not source_url.startswith("https://"):
        return None
    return {
        "type": hotline_type,
        "name": name,
        "phone_number": phone,
        "alternate_phone": str(value.get("alternate_phone") or "").strip()[:60],
        "description": str(value.get("description") or "").strip()[:500],
        "source_name": source_name,
        "source_url": source_url,
    }


def national_hotlines():
    """Return admin-managed hotlines with immutable safety fallbacks.

    The initial values are the sourced records already shipped by the app.
    Admin edits are stored as a public SiteSetting so no provider or number is
    invented. Missing/invalid CMS rows are ignored and required national
    services are restored from that known source instead of disappearing.
    """
    baseline = {row["type"]: dict(row) for row in NATIONAL_HOTLINES}
    setting = SiteSetting.objects.filter(key=HOTLINE_SETTING_KEY, is_public=True).first()
    rows = []
    if setting and isinstance(setting.value, list):
        for value in setting.value:
            row = _hotline_row(value)
            if row and value.get("is_active", True):
                rows.append(row)
    by_type = {row["type"]: row for row in rows}
    for hotline_type in REQUIRED_HOTLINE_TYPES:
        if hotline_type not in by_type and hotline_type in baseline:
            by_type[hotline_type] = baseline[hotline_type]
    ordered = []
    for row in NATIONAL_HOTLINES:
        if row["type"] in by_type:
            ordered.append(by_type.pop(row["type"]))
    ordered.extend(by_type.values())
    return ordered


def save_national_hotlines(rows, user=None):
    cleaned = []
    for value in rows:
        row = _hotline_row(value)
        if row:
            row["is_active"] = bool(value.get("is_active", True))
            cleaned.append(row)
    setting, _ = SiteSetting.objects.update_or_create(
        key=HOTLINE_SETTING_KEY,
        defaults={
            "value": cleaned,
            "description": "Admin-managed national emergency hotlines; required dispatch services are protected.",
            "is_public": True,
            "updated_by": user,
        },
    )
    return setting


def is_nepal_coordinate(latitude, longitude):
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return False
    return 26 <= latitude <= 31 and 80 <= longitude <= 89



def _hours(value):
    from .opening_hours import status as hours_status
    return hours_status(value or "")

def clean_phone(value, fallback):
    value = str(value or "").strip()
    if not value or value.lower() in {"nan", "none", "null"}:
        return fallback, bool(fallback)
    if value.endswith(".0"):
        value = value[:-2]
    if is_placeholder_phone(value):  # templated dataset filler, not a real number
        return fallback, bool(fallback)
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
    ranked.sort(key=lambda pair: (getattr(pair[1], "is_approximate_coordinate", False), pair[0]))
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


# ---------------------------------------------------------------------------
# Cached "nearest hospital / police" lookup
# ---------------------------------------------------------------------------
# build_emergency_directory() above is the full emergency-page payload: it also
# ranks every EmergencyContact (with no spatial filter at all) and every OSM
# essential service. That is correct for /emergency, but far too expensive for
# callers that only need the nearest hospital and police station — the AI
# recommendation view used it once per result, which cost ~5.6 s per call and
# over 100 s per request.
#
# The snapshot below loads both tables once, reuses them briefly, and answers
# from a small spatial grid. Item keys match the full directory.
_FACILITY_CACHE = {"signature": None, "rows": [], "grid": None, "checked_at": 0.0}
_FACILITY_RECHECK_SECONDS = 60.0
_FACILITY_FIELDS = (
    "id", "name", "address", "district", "phone", "latitude", "longitude",
    "opening_hours", "emergency_available", "is_verified", "verified_at",
    "updated_at", "source_name", "source_url", "coordinate_status",
)


def _facility_signature():
    return (
        Hospital.objects.filter(is_archived=False).aggregate(n=Count("id"), m=Max("updated_at")),
        PoliceStation.objects.filter(is_archived=False).aggregate(n=Count("id"), m=Max("updated_at")),
    )


class _PointGrid:
    """Small spatial hash so nearest-facility lookups stay cheap."""

    CELL = 0.25  # degrees, about 27 km

    def __init__(self, rows):
        self.cells = {}
        for row in rows:
            try:
                cell = (int(float(row["latitude"]) // self.CELL), int(float(row["longitude"]) // self.CELL))
            except (TypeError, ValueError):
                continue
            self.cells.setdefault(cell, []).append(row)

    def nearest(self, lat, lng, kinds):
        ci, cj = int(lat // self.CELL), int(lng // self.CELL)
        best = {}
        for ring in range(0, 5):
            for i in range(ci - ring, ci + ring + 1):
                for j in range(cj - ring, cj + ring + 1):
                    if max(abs(i - ci), abs(j - cj)) != ring:
                        continue
                    for row in self.cells.get((i, j), ()):
                        kind = row["_kind"]
                        if kind not in kinds:
                            continue
                        distance = haversine_distance(lat, lng, row["latitude"], row["longitude"])
                        if kind not in best or distance < best[kind][0]:
                            best[kind] = (distance, row)
            if len(best) >= len(kinds):
                break
        return best


def _facility_snapshot():
    """(rows, grid) from a short-lived cache."""
    now = time.monotonic()
    if (
        _FACILITY_CACHE["signature"] is not None
        and now - _FACILITY_CACHE["checked_at"] < _FACILITY_RECHECK_SECONDS
    ):
        return _FACILITY_CACHE["rows"], _FACILITY_CACHE["grid"]
    hospitals = list(Hospital.objects.filter(is_archived=False).values(*_FACILITY_FIELDS))
    police = list(PoliceStation.objects.filter(is_archived=False).values(*_FACILITY_FIELDS))
    rows = [dict(row, _kind="hospital") for row in hospitals]
    rows += [dict(row, _kind="police") for row in police]
    grid = _PointGrid(rows)
    _FACILITY_CACHE.update(
        signature=_facility_signature(), rows=rows, grid=grid, checked_at=now
    )
    return rows, grid


def _is_approximate(row):
    """Same rule as the model's ``is_approximate_coordinate`` property.

    Recomputed here because a ``.values()`` snapshot cannot carry a Python
    property, and dropping the flag would mislabel an approximate area-point
    coordinate as an exact facility position.
    """
    status = row.get("coordinate_status")
    if status == "APPROXIMATE":
        return True
    if status in ("VERIFIED", "EXACT", "OFFICIAL"):
        return False
    return row.get("latitude") is None or row.get("longitude") is None


def _facility_item(row, distance, radius_km):
    is_approx = _is_approximate(row)
    distance = round(distance, 2)
    outside = distance > radius_km
    phone, _ = clean_phone(row.get("phone"), "")
    dist_label = f"≈ {distance} km (area point)" if is_approx else f"{distance} km"
    return {
        "id": f"{row['_kind']}-{row['id']}", "type": row["_kind"], "name": row.get("name") or "",
        "address": row.get("address") or "", "district": row.get("district") or "",
        "phone_number": phone, "phone_is_national_fallback": False,
        "latitude": float(row["latitude"]), "longitude": float(row["longitude"]),
        "distance_km": distance, "distance_label": dist_label,
        "km": distance, "is_approximate": is_approx,
        "outside_requested_radius": outside,
        "image_url": None,
        "opening_hours": row.get("opening_hours"),
        "hours": _hours(row.get("opening_hours")),
        "emergency_available": row.get("emergency_available"),
        "verified": bool(row.get("is_verified")), "verified_at": row.get("verified_at"),
        "updated_at": row.get("updated_at"),
        "source_name": row.get("source_name") or "", "source_url": row.get("source_url") or "",
        "estimated_travel_time_min": max(1, round(distance / 30 * 60)),
        "travel_time_basis": "Rough estimate: straight-line distance at 30 km/h — not a road route",
    }


def nearest_facilities(latitude, longitude, radius_km=100, kinds=("hospital", "police")):
    """Nearest hospital / police station per requested kind.

    Same item shape as ``build_emergency_directory`` but answered from a cached
    snapshot instead of re-querying and re-ranking every emergency contact and
    OSM service row on each call.
    """
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return {kind: None for kind in kinds}
    if not is_nepal_coordinate(latitude, longitude):
        return {kind: None for kind in kinds}
    _rows, grid = _facility_snapshot()
    hits = grid.nearest(latitude, longitude, set(kinds))
    return {
        kind: _facility_item(hits[kind][1], hits[kind][0], radius_km) if kind in hits else None
        for kind in kinds
    }


def build_emergency_directory(latitude, longitude, destination=None, radius_km=50, limit=8):
    latitude, longitude = float(latitude), float(longitude)
    if not is_nepal_coordinate(latitude, longitude):
        raise ValueError("Coordinates must be inside Nepal (latitude 26–31, longitude 80–89).")

    def _image_url(row):
        try:
            return row.image.url if row.image else None
        except (ValueError, AttributeError):
            return None

    def hospital_item(row, distance, outside_radius):
        phone, _ = clean_phone(row.phone, "")
        is_approx = getattr(row, "is_approximate_coordinate", False)
        dist_label = f"≈ {distance} km (area point)" if is_approx else f"{distance} km"
        return {
            "id": f"hospital-{row.id}", "type": "hospital", "name": row.name,
            "address": row.address, "district": row.district,
            "phone_number": phone, "phone_is_national_fallback": False,
            "latitude": float(row.latitude), "longitude": float(row.longitude),
            "distance_km": distance, "distance_label": dist_label,
            "is_approximate": is_approx,
            "outside_requested_radius": outside_radius,
            "image_url": _image_url(row),
            "opening_hours": row.opening_hours, "hours": _hours(row.opening_hours), "emergency_available": row.emergency_available,
            "verified": row.is_verified, "verified_at": row.verified_at, "updated_at": row.updated_at,
            "source_name": row.source_name or "",
            "source_url": row.source_url or "",
        }

    def police_item(row, distance, outside_radius):
        phone, _ = clean_phone(row.phone, "")
        is_approx = getattr(row, "is_approximate_coordinate", False)
        dist_label = f"≈ {distance} km (area point)" if is_approx else f"{distance} km"
        return {
            "id": f"police-{row.id}", "type": "police", "name": row.name,
            "address": row.address, "district": destination.district if destination else "",
            "phone_number": phone, "phone_is_national_fallback": False,
            "latitude": float(row.latitude), "longitude": float(row.longitude),
            "distance_km": distance, "distance_label": dist_label,
            "is_approximate": is_approx,
            "outside_requested_radius": outside_radius,
            "image_url": _image_url(row),
            "opening_hours": row.opening_hours, "hours": _hours(row.opening_hours), "emergency_available": row.emergency_available,
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
            "opening_hours": service.opening_hours, "hours": _hours(service.opening_hours),
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
        "national_hotlines": national_hotlines(),
        "national_hotlines_source": "Admin-managed records with required Nepal emergency fallbacks",
        "coverage_gap": coverage_gap,
        "local_coverage_note": (
            "Local facilities are returned only when a sourced coordinate record exists. "
            "National hotlines remain available for every valid Nepal coordinate."
        ),
        "notice": notice,
    }
