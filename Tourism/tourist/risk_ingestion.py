"""Provider-neutral ingestion for DHM, BIPAD and verified Nepal risk feeds.

Adapters normalize authoritative payloads into this schema; this module never
scrapes pages or upgrades an unverified report into an official warning.
"""
from datetime import date

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .emergency_service import resolve_destination
from .models import CurrentHazard, Destination, RiskIncident, RiskObservation
from .utils import haversine_distance

PROVIDERS = {
    "dhm": {"name": "Department of Hydrology and Meteorology", "source_type": "official"},
    "bipad": {"name": "BIPAD Portal", "source_type": "official"},
    "admin": {"name": "Tourism Admin", "source_type": "admin"},
    "news": {"name": "Verified News Report", "source_type": "news"},
}


def _datetime(value, default=None):
    if not value:
        return default
    parsed = parse_datetime(str(value))
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed or default


def _destination(record):
    ref = record.get("destination_id") or record.get("destination_slug") or record.get("destination_name")
    destination = resolve_destination(ref) if ref else None
    if destination or record.get("latitude") is None or record.get("longitude") is None:
        return destination
    lat, lon = float(record["latitude"]), float(record["longitude"])
    ranked = []
    for item in Destination.objects.filter(is_active=True, status="approved").exclude(latitude__isnull=True):
        ranked.append((haversine_distance(lat, lon, item.latitude, item.longitude), item))
    ranked.sort(key=lambda pair: pair[0])
    return ranked[0][1] if ranked else None


def ingest_records(records, provider_key, verified=False):
    provider = PROVIDERS.get(provider_key)
    if not provider:
        raise ValueError(f"Unknown provider '{provider_key}'. Register it before ingestion.")
    summary = {"current_created": 0, "historical_created": 0, "observations_created": 0, "skipped": 0}
    for record in records:
        destination = _destination(record)
        kind = record.get("record_kind", "current")
        required = bool(record.get("observation_type") and record.get("value") is not None and record.get("unit")) if kind == "observation" else bool(record.get("title") and record.get("hazard_type"))
        if not destination or not required:
            summary["skipped"] += 1; continue
        source_name = record.get("source_name") or provider["name"]
        source_url = record.get("source_url", "")
        source_type = record.get("source_type") or provider["source_type"]
        is_verified = bool(verified and source_url and source_type in {"official", "admin", "news", "api"})
        if kind == "observation":
            observed_at = _datetime(record.get("observed_at"), timezone.now())
            _, created = RiskObservation.objects.update_or_create(
                destination=destination, observation_type=record["observation_type"],
                station_name=record.get("station_name") or source_name, observed_at=observed_at,
                defaults={
                    "value": float(record["value"]), "unit": record["unit"],
                    "trend": record.get("trend", "unknown"),
                    "station_latitude": record.get("station_latitude"),
                    "station_longitude": record.get("station_longitude"),
                    "distance_km": record.get("distance_km"), "source_type": source_type,
                    "source_name": source_name, "source_url": source_url,
                    "published_at": _datetime(record.get("published_at")), "verified": is_verified,
                },
            )
            summary["observations_created"] += int(created)
        elif kind == "historical":
            event_date = parse_date(str(record.get("event_date", ""))) or date.today()
            _, created = RiskIncident.objects.update_or_create(
                destination=destination, title=record["title"], event_date=event_date,
                source_name=source_name,
                defaults={
                    "hazard_type": record["hazard_type"], "description": record.get("description", ""),
                    "severity": record.get("severity", "moderate"), "source_type": source_type,
                    "source_url": source_url, "published_at": _datetime(record.get("published_at")),
                    "latitude": record.get("latitude"), "longitude": record.get("longitude"),
                    "municipality": record.get("municipality", ""), "affected_area": record.get("affected_area", ""),
                    "fatalities": max(0, int(record.get("fatalities", 0))),
                    "injuries": max(0, int(record.get("injuries", 0))), "verified": is_verified,
                },
            )
            summary["historical_created"] += int(created)
        else:
            observed_at = _datetime(record.get("observed_at"), timezone.now())
            _, created = CurrentHazard.objects.update_or_create(
                destination=destination, title=record["title"], source_name=source_name,
                observed_at=observed_at,
                defaults={
                    "hazard_type": record["hazard_type"], "description": record.get("description", ""),
                    "severity": record.get("severity", "moderate"), "source_type": source_type,
                    "source_url": source_url, "published_at": _datetime(record.get("published_at")),
                    "affected_area": record.get("affected_area", ""),
                    "expires_at": _datetime(record.get("expires_at")),
                    "station_name": record.get("station_name", ""), "distance_km": record.get("distance_km"),
                    "is_active": record.get("is_active", True), "verified": is_verified,
                },
            )
            summary["current_created"] += int(created)
    return summary
