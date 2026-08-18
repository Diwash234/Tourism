"""Moderation, publication and CSV synchronization for community data."""
import csv
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .models import (
    Category, Destination, DestinationImage, DestinationTransitRoute, Hotel,
    Hospital, InfrastructureSubmission, OSMEssentialService, PoliceStation,
    TravelExpenseFeedback, TravelRiskFeedback,
)
from .utils import haversine_distance

ROOT = Path(settings.BASE_DIR).parent


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
        if submission.image:
            DestinationImage.objects.create(
                destination=obj, image=submission.image.name, caption=submission.name,
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
            cover_image=submission.image.name if submission.image else None,
        )
    elif place_type == InfrastructureSubmission.PlaceType.HOSPITAL:
        obj = Hospital.objects.create(
            destination=destination, name=submission.name, phone=submission.phone,
            address=submission.address, district=submission.district,
            latitude=submission.latitude, longitude=submission.longitude,
            image=submission.image.name if submission.image else None,
        )
    elif place_type == InfrastructureSubmission.PlaceType.POLICE:
        obj = PoliceStation.objects.create(
            destination=destination, name=submission.name, phone=submission.phone,
            address=submission.address, latitude=submission.latitude, longitude=submission.longitude,
            image=submission.image.name if submission.image else None,
        )
    else:
        obj = OSMEssentialService.objects.create(
            osm_id=f"community/{submission.id}", category=place_type, name=submission.name,
            phone=submission.phone, address=submission.address,
            latitude=submission.latitude, longitude=submission.longitude,
            image=submission.image.name if submission.image else None,
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
    for record in TravelExpenseFeedback.objects.filter(is_employee_verified=True).select_related("destination"):
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
