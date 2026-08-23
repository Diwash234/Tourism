"""Recorded destination location helpers.

Fills missing city/coords only from other stored destinations, then writes
Tourism/dataset/destination_locations.json so Git clones can re-apply the
same fields without committing the local SQLite file.
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db.models import Avg, Q
from django.utils import timezone

from .models import Destination
from .utils import haversine_distance

KTM = (27.7172, 85.3240)
LOCATIONS_RELATIVE = Path("dataset") / "destination_locations.json"
SKIP_CITY_TOKENS = {"", "nepal", "province", "nan", "none", "null", "undefined"}
NEIGHBOUR_KM = 25
# ~111 km per degree of latitude; longitude is similar across Nepal.
NEIGHBOUR_DEG = NEIGHBOUR_KM / 111.0


def locations_path():
    return Path(settings.BASE_DIR) / LOCATIONS_RELATIVE


def _in_automated_test():
    return any(arg == "test" for arg in sys.argv)


def _in_nepal(lat, lng):
    try:
        latitude, longitude = float(lat), float(lng)
    except (TypeError, ValueError):
        return False
    return 26 <= latitude <= 31 and 80 <= longitude <= 89


def _clean_place(value):
    text = str(value or "").strip()
    if not text:
        return ""
    token = text.replace(",", "/").split("/")[0].strip()
    if token.lower() in SKIP_CITY_TOKENS or len(token) > 80:
        return ""
    return token[:100]


def _has_city(dest):
    return bool(str(dest.city or "").strip())


def fill_city_from_records(dest):
    """Set dest.city from municipality / district / nearest recorded neighbour."""
    if _has_city(dest):
        return False
    for candidate in (dest.municipality, dest.city_english, dest.city_nepali, dest.district):
        token = _clean_place(candidate)
        if token:
            dest.city = token
            return True
    if dest.latitude is None or dest.longitude is None:
        return False
    try:
        lat = float(dest.latitude)
        lng = float(dest.longitude)
    except (TypeError, ValueError):
        return False
    neighbours = Destination.objects.filter(
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False,
        latitude__gte=lat - NEIGHBOUR_DEG,
        latitude__lte=lat + NEIGHBOUR_DEG,
        longitude__gte=lng - NEIGHBOUR_DEG,
        longitude__lte=lng + NEIGHBOUR_DEG,
    ).exclude(pk=dest.pk).exclude(Q(city__isnull=True) | Q(city="")).only(
        "city", "latitude", "longitude",
    )
    best = None
    best_km = NEIGHBOUR_KM
    for other in neighbours.iterator(chunk_size=500):
        km = haversine_distance(lat, lng, other.latitude, other.longitude)
        if km is None or km > best_km:
            continue
        token = _clean_place(other.city)
        if not token:
            continue
        best = token
        best_km = km
        if km < 1:
            break
    if not best:
        return False
    dest.city = best
    return True


def fill_coords_from_records(dest):
    if dest.latitude is not None and dest.longitude is not None and _in_nepal(dest.latitude, dest.longitude):
        return False
    lat = lng = None
    twin = Destination.objects.filter(
        name__iexact=dest.name, latitude__isnull=False, longitude__isnull=False,
    ).exclude(pk=dest.pk).first()
    if twin and _in_nepal(twin.latitude, twin.longitude):
        lat, lng = twin.latitude, twin.longitude
    else:
        tokens = []
        for raw in (dest.district, dest.city, dest.province, dest.municipality):
            token = _clean_place(raw)
            if token and token not in tokens:
                tokens.append(token)
        for token in tokens:
            agg = Destination.objects.filter(
                district__iexact=token, latitude__isnull=False, longitude__isnull=False,
            ).aggregate(lat=Avg("latitude"), lng=Avg("longitude"))
            if agg["lat"] is None:
                agg = Destination.objects.filter(
                    city__iexact=token, latitude__isnull=False, longitude__isnull=False,
                ).aggregate(lat=Avg("latitude"), lng=Avg("longitude"))
            if agg["lat"] is not None and agg["lng"] is not None:
                lat, lng = agg["lat"], agg["lng"]
                break
    if lat is None or lng is None or not _in_nepal(lat, lng):
        return False
    dest.latitude = Decimal(str(round(float(lat), 6)))
    dest.longitude = Decimal(str(round(float(lng), 6)))
    return True


def fill_ktm_distance(dest):
    if dest.distance_from_kathmandu_km or dest.latitude is None or dest.longitude is None:
        return False
    km = haversine_distance(KTM[0], KTM[1], float(dest.latitude), float(dest.longitude))
    if km is None:
        return False
    dest.distance_from_kathmandu_km = Decimal(str(round(km, 2)))
    return True


def destination_location_row(dest):
    return {
        "id": dest.id,
        "name": dest.name,
        "slug": dest.slug,
        "city": dest.city or "",
        "city_english": dest.city_english or "",
        "city_nepali": dest.city_nepali or "",
        "district": dest.district or "",
        "province": dest.province or "",
        "municipality": dest.municipality or "",
        "ward_number": dest.ward_number,
        "latitude": float(dest.latitude) if dest.latitude is not None else None,
        "longitude": float(dest.longitude) if dest.longitude is not None else None,
        "distance_from_kathmandu_km": (
            float(dest.distance_from_kathmandu_km)
            if dest.distance_from_kathmandu_km is not None else None
        ),
    }


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
    return path


def export_destination_locations():
    path = locations_path()
    rows = {}
    qs = Destination.objects.filter(is_active=True).order_by("slug")
    for dest in qs.iterator(chunk_size=500):
        if not dest.slug:
            continue
        rows[dest.slug] = destination_location_row(dest)
    payload = {
        "generated_at": timezone.now().isoformat(),
        "count": len(rows),
        "note": (
            "Recorded destination locations. Clones apply this file with: "
            "python manage.py fill_missing_place_coords. "
            "Tourism/db.sqlite3 stays local and is not the Git source of these fills."
        ),
        "destinations": rows,
    }
    _write_json(path, payload)
    return path, len(rows)


def apply_destination_locations():
    path = locations_path()
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    rows = payload.get("destinations") or {}
    if not rows:
        return 0
    dests_by_slug = {
        dest.slug: dest
        for dest in Destination.objects.filter(slug__in=list(rows.keys()))
    }
    unmatched_names = [
        row["name"] for slug, row in rows.items()
        if slug not in dests_by_slug and row.get("name")
    ]
    dests_by_name = {}
    if unmatched_names:
        for dest in Destination.objects.filter(name__in=unmatched_names):
            dests_by_name.setdefault(dest.name.lower(), dest)
    applied = 0
    for slug, row in rows.items():
        dest = dests_by_slug.get(slug)
        if dest is None and row.get("name"):
            dest = dests_by_name.get(str(row["name"]).lower())
        if dest is None:
            continue
        changed = []
        if not _has_city(dest) and row.get("city"):
            dest.city = str(row["city"])[:100]
            changed.append("city")
        if not dest.city_english and row.get("city_english"):
            dest.city_english = str(row["city_english"])[:200]
            changed.append("city_english")
        if not dest.city_nepali and row.get("city_nepali"):
            dest.city_nepali = str(row["city_nepali"])[:200]
            changed.append("city_nepali")
        if not dest.district and row.get("district"):
            dest.district = str(row["district"])[:100]
            changed.append("district")
        if not dest.province and row.get("province"):
            dest.province = str(row["province"])[:100]
            changed.append("province")
        if not dest.municipality and row.get("municipality"):
            dest.municipality = str(row["municipality"])[:150]
            changed.append("municipality")
        if dest.ward_number is None and row.get("ward_number") is not None:
            try:
                dest.ward_number = int(row["ward_number"])
                changed.append("ward_number")
            except (TypeError, ValueError):
                pass
        if dest.latitude is None and row.get("latitude") is not None and _in_nepal(row.get("latitude"), row.get("longitude")):
            dest.latitude = Decimal(str(row["latitude"]))
            dest.longitude = Decimal(str(row["longitude"]))
            changed.extend(["latitude", "longitude"])
        if dest.distance_from_kathmandu_km is None and row.get("distance_from_kathmandu_km") is not None:
            dest.distance_from_kathmandu_km = Decimal(str(row["distance_from_kathmandu_km"]))
            changed.append("distance_from_kathmandu_km")
        if changed:
            dest.save(update_fields=changed + ["updated_at"])
            applied += 1
    return applied


def upsert_destination_location(destination):
    """Patch one destination into destination_locations.json after an admin edit."""
    if _in_automated_test() or not destination.slug:
        return None
    path = locations_path()
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            payload = {"destinations": {}}
    else:
        payload = {
            "generated_at": timezone.now().isoformat(),
            "count": 0,
            "note": "Recorded destination locations. Apply with: python manage.py fill_missing_place_coords",
            "destinations": {},
        }
    payload.setdefault("destinations", {})[destination.slug] = destination_location_row(destination)
    payload["count"] = len(payload["destinations"])
    payload["generated_at"] = timezone.now().isoformat()
    return _write_json(path, payload)


def sync_admin_destination_json(destination):
    """Keep the admin data.json snapshot in step with SQLite edits."""
    if _in_automated_test():
        return None
    path = Path(settings.BASE_DIR) / "dataset" / "data.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"destinations": {}}
    except (json.JSONDecodeError, OSError):
        existing = {"destinations": {}}
    existing.setdefault("destinations", {})[str(destination.id)] = {
        **destination_location_row(destination),
        "description": destination.description,
        "short_description": destination.short_description,
        "status": destination.status,
        "updated_at": destination.updated_at.isoformat() if destination.updated_at else None,
        "images": [
            {
                "id": image.id,
                "url": image.external_url or (image.image.url if image.image else ""),
                "caption": image.caption,
                "is_cover": image.is_cover,
                "status": image.verification_status,
            }
            for image in destination.gallery.all()[:100]
        ],
    }
    _write_json(path, existing)
    upsert_destination_location(destination)
    return path
