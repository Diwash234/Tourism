"""Moderation, publication and CSV synchronization for community data."""
import csv
import re
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Category, Destination, DestinationImage, DestinationTransitRoute, Hotel,
    Hospital, InfrastructureSubmission, OSMEssentialService, PoliceStation,
    TravelExpenseFeedback, TravelRiskFeedback,
)
from .utils import haversine_distance

ROOT = Path(settings.BASE_DIR).parent

DUPLICATE_DISTANCE_KM = 0.35
PHONE_MATCH_DISTANCE_KM = 1.0


class DuplicateEmergency(ValueError):
    """Raised when an official emergency row already exists in the DB or CSV."""

    def __init__(self, message, existing=None, kind="", csv_hit=False):
        super().__init__(message)
        self.existing = existing
        self.kind = kind
        self.csv_hit = csv_hit


def normalize_name(value):
    text = str(value or "").casefold()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def phone_digits(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if digits.startswith("977") and len(digits) > 7:
        digits = digits[3:]
    return digits.lstrip("0")


def names_match(left, right):
    first, second = normalize_name(left), normalize_name(right)
    if not first or not second:
        return False
    if first == second:
        return True
    shorter, longer = (first, second) if len(first) <= len(second) else (second, first)
    return len(shorter) >= 8 and shorter in longer


def _emergency_queryset(kind):
    if kind == "hospital":
        return Hospital.objects.all()
    if kind == "police":
        return PoliceStation.objects.all()
    return OSMEssentialService.objects.filter(category=kind)


def find_duplicate_emergency(kind, name, latitude, longitude, phone="", address=""):
    """Match an existing DB row by normalized name + type + nearby coords or phone."""
    target_phone = phone_digits(phone)
    for obj in _emergency_queryset(kind):
        distance = haversine_distance(latitude, longitude, obj.latitude, obj.longitude)
        distance = 9999 if distance is None else distance
        same_name = names_match(name, obj.name)
        obj_phone = phone_digits(getattr(obj, "phone", ""))
        same_phone = bool(target_phone and obj_phone and len(target_phone) >= 7 and target_phone == obj_phone)
        same_address = bool(address and names_match(address, getattr(obj, "address", "")))
        if same_name and distance <= DUPLICATE_DISTANCE_KM:
            return obj
        if same_name and same_phone:
            return obj
        if same_phone and distance <= PHONE_MATCH_DISTANCE_KM:
            return obj
        if same_name and same_address and distance <= 2.0:
            return obj
    return None


def _csv_rows(path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        try:
            return list(csv.DictReader(handle))
        except csv.Error:
            return []


def find_csv_duplicate(kind, name, latitude, longitude, phone=""):
    """Prevent a second official CSV row for the same facility."""
    target_phone = phone_digits(phone)
    checks = []
    if kind == "hospital":
        checks.extend([
            (ROOT / "Tourism" / "dataset" / "hospital_cleaned.csv", "hospital_name", None),
            (ROOT / "ml_service" / "data" / "emergency" / "hospital_cleaned.csv", "hospital_name", None),
        ])
    elif kind == "police":
        checks.append((ROOT / "Tourism" / "dataset" / "police_station_cleaned.csv", "police_station", None))
    checks.extend([
        (ROOT / "Tourism" / "dataset" / "community_services.csv", "name", kind),
        (ROOT / "ml_service" / "data" / "emergency" / "community_services.csv", "name", kind),
    ])
    for path, name_field, expected_type in checks:
        for row in _csv_rows(path):
            if expected_type:
                row_kind = str(row.get("place_type") or "").strip().lower()
                if row_kind and row_kind != expected_type:
                    continue
            try:
                row_lat = float(row.get("latitude"))
                row_lng = float(row.get("longitude"))
            except (TypeError, ValueError):
                continue
            distance = haversine_distance(latitude, longitude, row_lat, row_lng)
            distance = 9999 if distance is None else distance
            same_name = names_match(name, row.get(name_field) or "")
            row_phone = phone_digits(row.get("phone"))
            same_phone = bool(target_phone and row_phone and len(target_phone) >= 7 and target_phone == row_phone)
            if (same_name and distance <= DUPLICATE_DISTANCE_KM) or (same_name and same_phone) or (same_phone and distance <= PHONE_MATCH_DISTANCE_KM):
                return row
    return None


def _nearest_destination(submission):
    if submission.destination_id:
        return submission.destination
    ranked = []
    for destination in Destination.objects.filter(
        is_active=True, status=Destination.SubmissionStatus.APPROVED,
    ).exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        distance = haversine_distance(
            submission.latitude, submission.longitude,
            destination.latitude, destination.longitude,
        )
        ranked.append((distance, destination))
    ranked.sort(key=lambda pair: pair[0])
    return ranked[0][1] if ranked else None


def _append_unique(path, fieldnames, row, unique_fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    existing_keys = set()
    if exists:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            try:
                for old in csv.DictReader(handle):
                    existing_keys.add(tuple(str(old.get(key, "")).strip().lower() for key in unique_fields))
            except csv.Error:
                pass
    key = tuple(str(row.get(name, "")).strip().lower() for name in unique_fields)
    if key in existing_keys:
        return False
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fieldnames})
    return True


def sync_submission_csv(submission, published):
    service_fields = [
        "submission_id", "place_type", "name", "phone", "website", "address",
        "city", "municipality", "municipality_type", "ward_number", "district",
        "province", "latitude", "longitude", "destination", "transport_mode",
        "route_origin", "travel_time_minutes", "distance_km", "road_condition",
        "price_npr", "opening_hours", "image", "video", "approved_at",
    ]
    row = {
        "submission_id": submission.id, "place_type": submission.place_type,
        "name": submission.name, "phone": submission.phone, "website": submission.website,
        "address": submission.address, "city": submission.city,
        "municipality": submission.municipality, "municipality_type": submission.municipality_type,
        "ward_number": submission.ward_number or "", "district": submission.district,
        "province": submission.province, "latitude": submission.latitude,
        "longitude": submission.longitude,
        "destination": submission.destination.name if submission.destination else "",
        "transport_mode": submission.transport_mode, "route_origin": submission.route_origin,
        "travel_time_minutes": submission.travel_time_minutes or "",
        "distance_km": submission.distance_km or "", "road_condition": submission.road_condition,
        "price_npr": submission.price_npr or "", "opening_hours": submission.opening_hours,
        "image": submission.image.name if submission.image else "",
        "video": submission.video.name if submission.video else "",
        "approved_at": timezone.now().isoformat(),
    }
    for path in [
        ROOT / "Tourism" / "dataset" / "community_services.csv",
        ROOT / "ml_service" / "data" / "emergency" / "community_services.csv",
    ]:
        _append_unique(path, service_fields, row, ["submission_id"])

    if submission.place_type == InfrastructureSubmission.PlaceType.DESTINATION and published:
        tourism_fields = ["ID", "Name", "Type", "Tourism_Category", "Latitude", "Longitude", "City"]
        tourism_row = {
            "ID": published.id, "Name": published.name, "Type": "community",
            "Tourism_Category": published.category.name if published.category else "attraction",
            "Latitude": published.latitude, "Longitude": published.longitude, "City": published.city,
        }
        _append_unique(
            ROOT / "Tourism" / "dataset" / "destinations_clean.csv",
            tourism_fields, tourism_row, ["ID"],
        )
        ml_fields = tourism_fields + ["Area", "District", "Province", "search_text"]
        ml_row = {
            **tourism_row, "Area": published.municipality or "", "District": published.district or "",
            "Province": published.province or "",
            "search_text": f"{published.name} {published.city or ''} {published.district or ''} {published.province or ''} nepal".lower(),
        }
        _append_unique(
            ROOT / "ml_service" / "processed_data" / "destinations_clean.csv",
            ml_fields, ml_row, ["ID"],
        )

    if submission.route_origin and submission.destination:
        route_fields = [
            "submission_id", "origin", "destination", "district", "province",
            "transport_mode", "distance_km", "travel_time_minutes", "road_condition",
            "estimated_fare_npr", "source",
        ]
        route = {
            "submission_id": submission.id, "origin": submission.route_origin,
            "destination": submission.destination.name, "district": submission.district,
            "province": submission.province, "transport_mode": submission.transport_mode,
            "distance_km": submission.distance_km or "", "travel_time_minutes": submission.travel_time_minutes or "",
            "road_condition": submission.road_condition, "estimated_fare_npr": submission.price_npr or "",
            "source": "admin-approved community submission",
        }
        for path in [ROOT / "Tourism" / "dataset" / "community_routes.csv", ROOT / "ml_service" / "data" / "community_routes.csv"]:
            _append_unique(path, route_fields, route, ["submission_id"])

    submission.csv_synced_at = timezone.now()
    submission.save(update_fields=["csv_synced_at", "updated_at"])


def publish_submission(submission, reviewer, admin_note=""):
    if submission.status == InfrastructureSubmission.Status.APPROVED and submission.published_object_id:
        return submission
    destination = _nearest_destination(submission)
    place_type = submission.place_type
    primary_media = submission.media.filter(media_type="image").order_by("-is_primary", "created_at").first()
    primary_image = submission.image.name if submission.image else (primary_media.file.name if primary_media else None)
    obj = None

    if place_type == InfrastructureSubmission.PlaceType.DESTINATION:
        category, _ = Category.objects.get_or_create(name="Community Verified", defaults={"slug": "community-verified"})
        obj = Destination.objects.create(
            name=submission.name, category=category, description=submission.description,
            short_description=submission.description[:300], district=submission.district,
            province=submission.province, municipality=submission.municipality,
            ward_number=submission.ward_number, city=submission.city,
            latitude=submission.latitude, longitude=submission.longitude,
            address=submission.address, contact_phone=submission.phone or None,
            website=submission.website or None, created_by=submission.submitted_by,
            is_user_submitted=True, status=Destination.SubmissionStatus.APPROVED,
            source="Admin-approved community submission",
        )
        destination = obj
        if primary_image:
            DestinationImage.objects.create(
                destination=obj, image=primary_image, caption=submission.name,
                is_cover=True, source=DestinationImage.Source.USER_UPLOAD,
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_verified=True, uploaded_by=submission.submitted_by,
            )
    elif destination is None:
        raise ValueError("No destination is available to link this service.")
    elif place_type == InfrastructureSubmission.PlaceType.HOTEL:
        obj = Hotel.objects.create(
            destination=destination, name=submission.name, phone=submission.phone,
            address=submission.address, latitude=submission.latitude, longitude=submission.longitude,
            price_per_night=submission.price_npr, currency="NPR", source=Hotel.Source.MANUAL,
            booking_status=Hotel.BookingStatus.UNKNOWN,
            cover_image=primary_image,
            source_url=submission.website, is_verified=True, verified_at=timezone.now(),
        )
    elif place_type == InfrastructureSubmission.PlaceType.HOSPITAL:
        obj = Hospital.objects.create(
            destination=destination, name=submission.name, phone=submission.phone,
            address=submission.address, district=submission.district,
            latitude=submission.latitude, longitude=submission.longitude,
            image=primary_image,
            opening_hours=submission.opening_hours, source_name="Admin-approved community submission",
            source_url=submission.website, is_verified=True, verified_at=timezone.now(),
        )
    elif place_type == InfrastructureSubmission.PlaceType.POLICE:
        obj = PoliceStation.objects.create(
            destination=destination, name=submission.name, phone=submission.phone,
            address=submission.address, latitude=submission.latitude, longitude=submission.longitude,
            image=primary_image,
            opening_hours=submission.opening_hours, source_name="Admin-approved community submission",
            source_url=submission.website, is_verified=True, verified_at=timezone.now(),
        )
    else:
        obj = OSMEssentialService.objects.create(
            osm_id=f"community/{submission.id}", category=place_type, name=submission.name,
            phone=submission.phone, address=submission.address,
            latitude=submission.latitude, longitude=submission.longitude,
            image=primary_image,
            source_name="Admin-approved community submission", source_url=submission.website,
            is_verified=True, verified_at=timezone.now(), opening_hours=submission.opening_hours,
            emergency_available=place_type in {"fire_station", "ambulance", "blood_bank"},
            raw_tags={
                "source": "admin-approved community submission", "verified": True,
                "municipality": submission.municipality, "ward": submission.ward_number,
                "province": submission.province, "submission_id": submission.id,
            },
        )

    if destination and submission.route_origin:
        DestinationTransitRoute.objects.create(
            destination=destination, origin=submission.route_origin,
            transport_mode=submission.transport_mode or "Local transport",
            distance_km=submission.distance_km,
            approx_duration=f"{submission.travel_time_minutes} minutes" if submission.travel_time_minutes else "",
            road_condition=submission.road_condition,
            estimated_fare_npr=submission.price_npr,
            route_source="Admin-approved community submission",
        )
        submission.destination = destination

    if destination:
        submission.destination = destination
    submission.status = InfrastructureSubmission.Status.APPROVED
    submission.media.update(is_verified=True)
    submission.reviewed_by = reviewer
    submission.reviewed_at = timezone.now()
    submission.admin_note = admin_note
    submission.published_model = obj._meta.label
    submission.published_object_id = obj.pk
    submission.save()
    sync_submission_csv(submission, obj)
    return submission


def _merge_verified_risk_features(path, records):
    """Upsert verified traveler evidence into the existing risk CSV schema."""
    if not path.exists():
        return
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    normalized = {name.lower().replace(" ", "_"): name for name in fieldnames}
    place_col = normalized.get("place")
    if not place_col:
        return
    by_place = {str(row.get(place_col, "")).strip().lower(): row for row in rows}
    for record in records:
        destination = record.destination
        name = (record.destination_name or (destination.name if destination else "")).strip()
        key = name.lower()
        row = by_place.get(key)
        if row is None:
            row = {field: "0" for field in fieldnames}
            row[place_col] = name
            if destination:
                for normalized_name, value in [
                    ("latitude", destination.latitude), ("longitude", destination.longitude),
                    ("district", destination.district),
                ]:
                    if normalized.get(normalized_name):
                        row[normalized[normalized_name]] = value or ""
            rows.append(row); by_place[key] = row
        hazard = (record.hazard_witnessed or "").lower().replace(" ", "_")
        target = {
            "landslide": "landslide", "avalanche": "avalanche", "flood": "flood",
            "heavy_snow": "avalanche", "rockfall": "landslide",
        }.get(hazard)
        if record.accident_occurred and normalized.get("accidents"):
            col = normalized["accidents"]; row[col] = str(float(row.get(col) or 0) + 1)
        if target and normalized.get(target):
            col = normalized[target]; row[col] = str(float(row.get(col) or 0) + 1)
        indicator = max(0.0, min(100.0, (10.0 - float(record.overall_safety_rating or 0)) * 10.0))
        index_col = normalized.get("tourism_risk_index")
        if index_col:
            old = float(row.get(index_col) or 0); row[index_col] = str(round((old + indicator) / 2, 2))
        category_col = normalized.get("risk_category")
        if category_col:
            row[category_col] = "HIGH" if indicator >= 65 else "MODERATE" if indicator >= 35 else "LOW"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames); writer.writeheader(); writer.writerows(rows)


def _next_numeric_id(path, field="id"):
    highest = 0
    if not path.exists() or path.stat().st_size == 0:
        return 1
    with path.open(newline="", encoding="utf-8-sig") as handle:
        try:
            for row in csv.DictReader(handle):
                try:
                    highest = max(highest, int(float(row.get(field) or 0)))
                except (TypeError, ValueError):
                    continue
        except csv.Error:
            pass
    return highest + 1


def resolve_service_destination(latitude, longitude, destination_id=None, district="", city=""):
    if destination_id:
        destination = Destination.objects.filter(pk=destination_id).first()
        if destination:
            return destination
    qs = Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)
    if city:
        destination = qs.filter(Q(name__iexact=city) | Q(city__iexact=city) | Q(slug__iexact=city)).first()
        if destination:
            return destination
    if district:
        destination = qs.filter(district__iexact=district).order_by("-is_featured", "name").first()
        if destination:
            return destination

    class _Point:
        destination_id = None
        destination = None

        def __init__(self, lat, lng):
            self.latitude = lat
            self.longitude = lng

    return _nearest_destination(_Point(latitude, longitude))


def serialize_emergency_record(kind, obj):
    dest = getattr(obj, "destination", None)
    tags = getattr(obj, "raw_tags", None) or {}
    return {
        "kind": kind,
        "id": obj.id,
        "name": obj.name,
        "phone": getattr(obj, "phone", "") or "",
        "address": getattr(obj, "address", "") or "",
        "district": getattr(obj, "district", "") or (dest.district if dest else "") or tags.get("district", ""),
        "province": (dest.province if dest else "") or tags.get("province", ""),
        "latitude": float(obj.latitude),
        "longitude": float(obj.longitude),
        "source_url": getattr(obj, "source_url", "") or "",
        "verified": bool(getattr(obj, "is_verified", False)),
        "is_archived": bool(getattr(obj, "is_archived", False)),
        "destination_id": getattr(obj, "destination_id", None),
        "destination_name": dest.name if dest else "",
        "updated_at": getattr(obj, "updated_at", None),
        "opening_hours": getattr(obj, "opening_hours", "") or "",
    }


def publish_official_emergency(data, reviewer=None):
    """Admin-entered hospital / police / pharmacy / fire row — DB + official CSVs."""
    import uuid

    kind = str(data.get("kind") or "").strip().lower()
    if kind == "fire":
        kind = "fire_station"
    allowed = {"hospital", "police", "pharmacy", "fire_station", "ambulance", "blood_bank", "clinic"}
    if kind not in allowed:
        raise ValueError("kind must be hospital, police, pharmacy, fire_station, ambulance, blood_bank or clinic")
    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("name is required")
    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
    except (TypeError, ValueError) as exc:
        raise ValueError("latitude and longitude are required numbers") from exc
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("latitude/longitude out of range")
    phone = str(data.get("phone") or "").strip()[:50]
    address = str(data.get("address") or "").strip()[:300]
    district = str(data.get("district") or "").strip()[:100]
    province = str(data.get("province") or "").strip()[:120]
    city = str(data.get("city") or data.get("destination") or "").strip()[:120]
    source_url = str(data.get("source_url") or "").strip()
    if source_url and not source_url.startswith("https://"):
        raise ValueError("source_url must use HTTPS")
    opening_hours = str(data.get("opening_hours") or "")[:160]
    destination = resolve_service_destination(
        latitude, longitude, data.get("destination_id"), district, city or name,
    )
    if kind in {"hospital", "police"} and destination is None:
        raise ValueError("Link an approved destination or create one for this district first so the record can be mapped.")
    now = timezone.now()
    existing = find_duplicate_emergency(kind, name, latitude, longitude, phone=phone, address=address)
    csv_existing = find_csv_duplicate(kind, name, latitude, longitude, phone=phone)
    if existing or csv_existing:
        raise DuplicateEmergency(
            "An emergency record with this name and location already exists.",
            existing=existing,
            kind=kind,
            csv_hit=bool(csv_existing),
        )
    csv_written = {}
    if kind == "hospital":
        with transaction.atomic():
            obj = Hospital.objects.create(
                destination=destination, name=name[:200], address=address or district or "Nepal",
                phone=phone or "102", latitude=latitude, longitude=longitude,
                district=district or (destination.district or ""),
                opening_hours=opening_hours, source_name="Admin verified directory",
                source_url=source_url, is_verified=True, verified_at=now, is_archived=False,
            )
        hospital_fields = [
            "hospital_name", "address", "phone", "latitude", "longitude",
            "district", "destination", "province", "data_quality_score",
        ]
        hospital_row = {
            "hospital_name": name, "address": address, "phone": phone,
            "latitude": latitude, "longitude": longitude, "district": district,
            "destination": destination.name if destination else city,
            "province": province, "data_quality_score": 100,
        }
        for path in [
            ROOT / "Tourism" / "dataset" / "hospital_cleaned.csv",
            ROOT / "ml_service" / "data" / "emergency" / "hospital_cleaned.csv",
        ]:
            csv_written["hospital"] = _append_unique(path, hospital_fields, hospital_row, ["hospital_name", "latitude", "longitude"])
    elif kind == "police":
        with transaction.atomic():
            obj = PoliceStation.objects.create(
                destination=destination, name=name[:200], address=address or district or "Nepal",
                phone=phone or "100", latitude=latitude, longitude=longitude,
                opening_hours=opening_hours, source_name="Admin verified directory",
                source_url=source_url, is_verified=True, verified_at=now, is_archived=False,
            )
        police_path = ROOT / "Tourism" / "dataset" / "police_station_cleaned.csv"
        police_fields = [
            "id", "police_station", "destination", "address", "phone",
            "latitude", "longitude", "district", "province", "data_quality_score",
        ]
        police_row = {
            "id": _next_numeric_id(police_path), "police_station": name,
            "destination": destination.name if destination else city,
            "address": address, "phone": phone, "latitude": latitude, "longitude": longitude,
            "district": district or (destination.district if destination else ""),
            "province": province, "data_quality_score": 100,
        }
        csv_written["police"] = _append_unique(
            police_path, police_fields, police_row, ["police_station", "latitude", "longitude"],
        )
    else:
        with transaction.atomic():
            obj = OSMEssentialService.objects.create(
                osm_id=f"admin/{kind}/{uuid.uuid4().hex[:12]}", category=kind, name=name[:255],
                phone=phone, latitude=latitude, longitude=longitude, address=address,
                source_name="Admin verified directory", source_url=source_url,
                is_verified=True, verified_at=now, opening_hours=opening_hours, is_archived=False,
                emergency_available=kind in {"fire_station", "ambulance", "blood_bank"},
                raw_tags={"district": district, "province": province, "city": city, "source": "admin"},
            )

    service_fields = [
        "submission_id", "place_type", "name", "phone", "website", "address",
        "city", "municipality", "municipality_type", "ward_number", "district",
        "province", "latitude", "longitude", "destination", "transport_mode",
        "route_origin", "travel_time_minutes", "distance_km", "road_condition",
        "price_npr", "opening_hours", "image", "video", "approved_at",
    ]
    community_row = {
        "submission_id": f"admin-{kind}-{obj.id}", "place_type": kind, "name": name,
        "phone": phone, "website": source_url, "address": address, "city": city,
        "municipality": "", "municipality_type": "", "ward_number": "",
        "district": district, "province": province, "latitude": latitude, "longitude": longitude,
        "destination": destination.name if destination else city,
        "transport_mode": "", "route_origin": "", "travel_time_minutes": "",
        "distance_km": "", "road_condition": "", "price_npr": "",
        "opening_hours": opening_hours, "image": "", "video": "",
        "approved_at": now.isoformat(),
    }
    for path in [
        ROOT / "Tourism" / "dataset" / "community_services.csv",
        ROOT / "ml_service" / "data" / "emergency" / "community_services.csv",
    ]:
        csv_written["community"] = _append_unique(
            path, service_fields, community_row, ["submission_id"],
        )
    return obj, csv_written


def _merge_verified_budget_features(path, records):
    if not records or not path:
        return
    headers = ["Source", "Destination", "District", "Province", "Transport Cost (USD)", "Food Cost/Day (USD)", "Accommodation/Night (USD)", "Local Taxi/Rick"]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header_line = next(reader, None)
                existing_rows = [r for r in list(reader) if len(r) >= 4]
        except Exception:
            existing_rows = []

    dest_keys = {_norm(r[1]) for r in existing_rows if len(r) >= 2}

    new_rows = []
    USD_RATE = 133.0
    for r in records:
        dest_name = r.destination_name or (r.destination.name if r.destination else "User Travel")
        if _norm(dest_name) in dest_keys:
            continue
        district = r.destination.district if r.destination else ""
        province = r.destination.province if r.destination else ""
        people = max(1, r.num_people or 1)
        days = max(1, r.num_days or 1)

        accom_usd = round((float(r.accommodation_cost or 0) / days / people) / USD_RATE, 2)
        food_usd = round((float(r.food_cost or 0) / days / people) / USD_RATE, 2)
        transport_usd = round((float(r.travel_cost or 0) / people) / USD_RATE, 2)
        taxi_usd = round((float(r.extra_cost or 0) / days / people) / USD_RATE, 2)

        if accom_usd <= 0: accom_usd = 15.0
        if food_usd <= 0: food_usd = 10.0
        if transport_usd <= 0: transport_usd = 5.0
        if taxi_usd <= 0: taxi_usd = 3.0

        new_rows.append([
            "Verified User Report", dest_name, district, province,
            str(transport_usd), str(food_usd), str(accom_usd), str(taxi_usd)
        ])

    if new_rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(existing_rows + new_rows)


def export_verified_ml_feedback():
    budget_fields = [
        "record_id", "destination", "district", "province", "num_people", "num_days",
        "travel_mode", "accommodation_cost_npr", "travel_cost_npr", "entry_cost_npr",
        "food_cost_npr", "extra_cost_npr", "total_cost_npr", "route_details", "verified_at",
    ]
    risk_fields = [
        "record_id", "destination", "latitude", "longitude", "district", "became_sick",
        "sickness_type", "accident_occurred", "hazard_witnessed",
        "transport_accessibility_rating", "overall_safety_rating", "comments", "verified_at",
    ]
    counts = {"budget": 0, "risk": 0}
    verified_budget_records = list(
        TravelExpenseFeedback.objects.filter(is_employee_verified=True).select_related("destination")
    )
    for record in verified_budget_records:
        row = {
            "record_id": record.id, "destination": record.destination_name,
            "district": record.destination.district if record.destination else "",
            "province": record.destination.province if record.destination else "",
            "num_people": record.num_people, "num_days": record.num_days,
            "travel_mode": record.travel_mode, "accommodation_cost_npr": record.accommodation_cost,
            "travel_cost_npr": record.travel_cost, "entry_cost_npr": record.entry_cost,
            "food_cost_npr": record.food_cost, "extra_cost_npr": record.extra_cost,
            "total_cost_npr": record.total_cost, "route_details": record.route_details,
            "verified_at": record.updated_at.isoformat(),
        }
        for path in [ROOT / "Tourism" / "dataset" / "budget_estimation.csv", ROOT / "ml_service" / "data" / "budget" / "budget_estimation.csv"]:
            _append_unique(path, budget_fields, row, ["record_id"])
        counts["budget"] += 1

    for path in [
        ROOT / "Tourism" / "dataset" / "budget_features.csv",
        ROOT / "ml_service" / "processed_data" / "budget_features.csv",
    ]:
        _merge_verified_budget_features(path, verified_budget_records)

    verified_risk_records = list(
        TravelRiskFeedback.objects.filter(is_admin_verified=True).select_related("destination")
    )
    for record in verified_risk_records:
        destination = record.destination
        row = {
            "record_id": record.id, "destination": record.destination_name,
            "latitude": destination.latitude if destination else "", "longitude": destination.longitude if destination else "",
            "district": destination.district if destination else "", "became_sick": record.became_sick,
            "sickness_type": record.sickness_type, "accident_occurred": record.accident_occurred,
            "hazard_witnessed": record.hazard_witnessed,
            "transport_accessibility_rating": record.transport_accessibility_rating,
            "overall_safety_rating": record.overall_safety_rating, "comments": record.comments,
            "verified_at": record.reviewed_at.isoformat() if record.reviewed_at else record.updated_at.isoformat(),
        }
        for path in [ROOT / "Tourism" / "dataset" / "risk_feedback.csv", ROOT / "ml_service" / "data" / "risk" / "risk_feedback.csv"]:
            _append_unique(path, risk_fields, row, ["record_id"])
        counts["risk"] += 1
    for path in [
        ROOT / "Tourism" / "dataset" / "risk_features.csv",
        ROOT / "ml_service" / "processed_data" / "risk_features.csv",
    ]:
        _merge_verified_risk_features(path, verified_risk_records)
    return counts
