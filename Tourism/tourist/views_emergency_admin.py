"""Admin emergency directory: add accurate local services to the DB and official CSVs."""
import re
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.logging_services import log_action
from .community_data_service import (
    DuplicateEmergency,
    publish_official_emergency,
    resolve_service_destination,
    serialize_emergency_record,
)
from .models import Destination, Hospital, InfrastructureSubmission, OSMEssentialService, PoliceStation
from .permissions import IsAdminOrStaff
from .views_admin import _has_capability, _require_capability, _is_platform_admin, _scope_destination_queryset


def _normalize_kind(value):
    kind = str(value or "").strip().lower()
    if kind == "fire":
        return "fire_station"
    return kind


def _emergency_object(kind, pk):
    kind = _normalize_kind(kind)
    if kind == "hospital":
        return Hospital.objects.filter(pk=pk).first(), "hospital"
    if kind == "police":
        return PoliceStation.objects.filter(pk=pk).first(), "police"
    obj = OSMEssentialService.objects.filter(pk=pk).first()
    return obj, (obj.category if obj else kind)


def _scope_emergency_queryset(queryset, user, kind=""):
    """Keep emergency records inside the operator's district scope."""
    if _is_platform_admin(user):
        return queryset
    districts = list(getattr(getattr(user, "capability_profile", None), "managed_districts", []) or [])
    if not districts and getattr(user, "role", "") == "district_manager":
        value = getattr(user, "managed_district", "")
        districts = [value] if value else []
    if not districts:
        return queryset
    from django.db.models import Q
    if kind == "hospital":
        scope = Q()
        for district in districts:
            scope |= Q(district__iexact=district) | Q(destination__district__iexact=district)
        return queryset.filter(scope)
    if kind == "police":
        scope = Q()
        for district in districts:
            scope |= Q(destination__district__iexact=district)
        return queryset.filter(scope)
    return queryset


def _emergency_districts(user):
    districts = list(getattr(getattr(user, "capability_profile", None), "managed_districts", []) or [])
    if not districts and getattr(user, "role", "") == "district_manager":
        value = getattr(user, "managed_district", "")
        districts = [value] if value else []
    return [str(value).strip().casefold() for value in districts if str(value).strip()]


def _essential_in_districts(row, districts):
    if not districts:
        return True
    tags = row.raw_tags if isinstance(row.raw_tags, dict) else {}
    values = [row.address, tags.get("district", ""), tags.get("city", ""), tags.get("province", "")]
    return any(str(value or "").casefold() in districts for value in values)


def _can_access_emergency(request, obj):
    if _is_platform_admin(request.user):
        return True
    districts = list(getattr(getattr(request.user, "capability_profile", None), "managed_districts", []) or [])
    if not districts and getattr(request.user, "role", "") == "district_manager":
        value = getattr(request.user, "managed_district", "")
        districts = [value] if value else []
    if not districts:
        return True
    record_district = getattr(obj, "district", "") or getattr(getattr(obj, "destination", None), "district", "")
    return str(record_district or "").casefold() in {str(value).casefold() for value in districts}


def _submission_row(item):
    return {
        "id": item.id,
        "kind": item.place_type,
        "name": item.name,
        "phone": item.phone or "",
        "address": item.address or "",
        "district": item.district or "",
        "province": item.province or "",
        "latitude": float(item.latitude),
        "longitude": float(item.longitude),
        "status": item.status,
        "submitted_by": item.submitted_by.email if item.submitted_by else "",
        "created_at": item.created_at,
    }


class AdminEmergencyDirectoryView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "safety", "view")
        q = (request.query_params.get("q") or "").strip()
        district = (request.query_params.get("district") or "").strip()
        kind = _normalize_kind(request.query_params.get("kind"))

        hospitals = _scope_emergency_queryset(Hospital.objects.select_related("destination").order_by("-updated_at"), request.user, "hospital")
        police = _scope_emergency_queryset(PoliceStation.objects.select_related("destination").order_by("-updated_at"), request.user, "police")
        essentials = _scope_emergency_queryset(OSMEssentialService.objects.exclude(category__in=["hospital", "police"]).order_by("-updated_at"), request.user)
        operator_districts = _emergency_districts(request.user)
        if operator_districts and not _is_platform_admin(request.user):
            essentials = essentials.filter(
                Q(address__iregex=r"(" + "|".join(re.escape(value) for value in operator_districts) + r")")
            )
        if q:
            hospitals = hospitals.filter(
                Q(name__icontains=q) | Q(address__icontains=q) | Q(district__icontains=q) | Q(destination__name__icontains=q)
            )
            police = police.filter(
                Q(name__icontains=q) | Q(address__icontains=q) | Q(destination__name__icontains=q) | Q(destination__district__icontains=q)
            )
            essentials = essentials.filter(Q(name__icontains=q) | Q(address__icontains=q) | Q(phone__icontains=q))
        if district:
            hospitals = hospitals.filter(Q(district__icontains=district) | Q(destination__district__icontains=district))
            police = police.filter(destination__district__icontains=district)

        essential_rows = [
            row for row in essentials
            if not operator_districts or _is_platform_admin(request.user) or _essential_in_districts(row, operator_districts)
        ]
        rows = []
        if kind in {"", "hospital"}:
            rows.extend(serialize_emergency_record("hospital", row) for row in hospitals)
        if kind in {"", "police"}:
            rows.extend(serialize_emergency_record("police", row) for row in police)
        if kind not in {"hospital", "police"}:
            qs = [row for row in essential_rows if row.category == kind] if kind else essential_rows
            for row in qs:
                if district:
                    tags = row.raw_tags or {}
                    hay = f"{row.address} {tags.get('district', '')} {tags.get('province', '')}"
                    if district.lower() not in hay.lower():
                        continue
                rows.append(serialize_emergency_record(row.category, row))
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = max(10, min(100, int(request.query_params.get("page_size", 50))))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid pagination"}, status=400)
        total = len(rows)
        pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, pages)
        rows = rows[(page - 1) * page_size:page * page_size]

        pending = InfrastructureSubmission.objects.filter(
            status=InfrastructureSubmission.Status.PENDING,
            place_type__in=["hospital", "police", "pharmacy", "fire_station", "ambulance", "blood_bank", "clinic", "atm", "bank"],
        ).select_related("submitted_by")
        if operator_districts and not _is_platform_admin(request.user):
            pending_scope = Q()
            for district in operator_districts:
                pending_scope |= Q(district__iexact=district)
            pending = pending.filter(pending_scope)
        pending = pending.order_by("-created_at")[:50]

        return Response({
            "count": total,
            "page": page,
            "pages": pages,
            "page_size": page_size,
            "results": rows,
            "pending_submissions": [_submission_row(item) for item in pending],
            "coverage": {
                "hospitals": hospitals.filter(is_archived=False).count(),
                "police": police.filter(is_archived=False).count(),
                "pharmacy": sum(1 for row in essential_rows if row.category == "pharmacy" and not row.is_archived),
                "fire_station": sum(1 for row in essential_rows if row.category == "fire_station" and not row.is_archived),
                "ambulance": sum(1 for row in essential_rows if row.category == "ambulance" and not row.is_archived),
                "atm": sum(1 for row in essential_rows if row.category in {"atm", "bank"} and not row.is_archived),
            },
            "notice": (
                "Add only accurate records with coordinates. This does not scrape Google or Facebook, "
                "and it does not invent pharmacies per ward. Existing OpenStreetMap sync still applies."
            ),
        })

    def post(self, request):
        _require_capability(request, "safety", "add")
        destination_id = request.data.get("destination_id")
        if destination_id:
            destination = Destination.objects.filter(pk=destination_id).first()
            if not destination or not _can_access_emergency(request, destination):
                return Response({"detail": "Destination is outside your assigned district"}, status=403)
        can_verify = _has_capability(request, "safety", "approve")
        inferred_destination = None
        try:
            inferred_destination = resolve_service_destination(
                float(request.data.get("latitude")), float(request.data.get("longitude")),
                request.data.get("destination_id"), request.data.get("district"),
                request.data.get("city") or request.data.get("name"),
            )
        except (TypeError, ValueError):
            pass
        if inferred_destination and not _can_access_emergency(request, inferred_destination):
            return Response({"detail": "Resolved destination is outside your assigned district"}, status=403)
        requested_district = str(request.data.get("district") or "").strip().casefold()
        operator_districts = _emergency_districts(request.user)
        if operator_districts and not inferred_destination and requested_district not in operator_districts:
            return Response({"detail": "A district assignment is required for this record."}, status=403)
        try:
            obj, csv_written = publish_official_emergency(request.data, request.user, verified=can_verify)
        except DuplicateEmergency as exc:
            kind = _normalize_kind(request.data.get("kind")) or exc.kind
            payload = {
                "detail": str(exc),
                "duplicate": True,
                "csv_hit": exc.csv_hit,
            }
            if exc.existing is not None:
                payload["record"] = serialize_emergency_record(kind or getattr(exc.existing, "category", "hospital"), exc.existing)
            return Response(payload, status=409)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        kind = _normalize_kind(request.data.get("kind")) or getattr(obj, "category", "hospital")
        log_action(
            request, "emergency.create", category="admin",
            message=f"Added {kind} {obj.name}", obj=obj, extra={"kind": kind, "csv_written": csv_written, "verified": can_verify},
        )
        destination = getattr(obj, "destination", None)
        if destination:
            from .views_admin import _sync_destination_json
            _sync_destination_json(destination)
        return Response({
            "id": obj.id,
            "message": (
                "Saved to the emergency directory and appended to the official CSV."
                if csv_written else
                "Saved as an unverified candidate; CSV feeds were not changed until verification."
            ),
            "record": serialize_emergency_record(kind, obj),
            "csv_written": csv_written,
        }, status=201)

    def patch(self, request):
        action = str(request.data.get("action") or "").strip().lower()
        if action == "verify":
            _require_capability(request, "safety", "approve")
        elif action == "archive":
            _require_capability(request, "safety", "delete")
        else:
            _require_capability(request, "safety", "change")
        obj, kind = _emergency_object(request.data.get("kind"), request.data.get("id"))
        if not obj:
            return Response({"detail": "Emergency record not found"}, status=404)
        if not _can_access_emergency(request, obj):
            return Response({"detail": "Emergency record is outside your assigned district"}, status=403)
        before = {
            "name": getattr(obj, "name", ""), "phone": getattr(obj, "phone", ""),
            "address": getattr(obj, "address", ""), "is_verified": getattr(obj, "is_verified", False),
            "is_archived": getattr(obj, "is_archived", False),
        }
        if action == "verify":
            obj.is_verified = True
            obj.verified_at = timezone.now()
        elif action == "archive":
            obj.is_archived = True
        elif action == "restore":
            obj.is_archived = False
        for field in ("name", "phone", "address", "opening_hours", "source_name"):
            if field in request.data:
                value = str(request.data.get(field) or "").strip()
                if field == "phone" and kind in {"hospital", "police"} and not value:
                    return Response({"detail": "A real phone number is required; placeholder numbers are not allowed"}, status=400)
                setattr(obj, field, value[:300])
        if "emergency_available" in request.data:
            obj.emergency_available = str(request.data.get("emergency_available")).lower() in {"1", "true", "yes", "on"}
        if "source_url" in request.data:
            source_url = str(request.data.get("source_url") or "").strip()
            if source_url and not source_url.startswith("https://"):
                return Response({"detail": "source_url must use HTTPS"}, status=400)
            obj.source_url = source_url
        if "latitude" in request.data or "longitude" in request.data:
            try:
                latitude = float(request.data.get("latitude", obj.latitude))
                longitude = float(request.data.get("longitude", obj.longitude))
            except (TypeError, ValueError):
                return Response({"detail": "latitude and longitude are required numbers"}, status=400)
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return Response({"detail": "latitude/longitude out of range"}, status=400)
            obj.latitude = latitude
            obj.longitude = longitude
        if kind == "hospital" and "district" in request.data:
            obj.district = str(request.data.get("district") or "")[:100]
        if action == "verify" and kind in {"hospital", "police"} and not str(getattr(obj, "phone", "") or "").strip():
            return Response({"detail": "A real phone number is required before this record can be verified."}, status=400)
        obj.save()
        destination = getattr(obj, "destination", None)
        if destination:
            from .views_admin import _sync_destination_json
            _sync_destination_json(destination)
        from audit.models import AuditLog
        AuditLog.objects.create(
            user=request.user, user_email=request.user.email,
            actor_role=getattr(request.user, "role", ""), category="safety",
            severity="warning" if action in {"verify", "archive"} else "info",
            source="backend", action=f"emergency.{action or 'update'}",
            message=f"{action.title() if action else 'Updated'} {kind} {obj.name}",
            object_type=type(obj).__name__, object_id=str(obj.pk),
            extra={"before": before, "kind": kind, "action": action},
        )
        log_action(
            request, f"emergency.{action or 'update'}", category="admin",
            message=f"{action or 'Updated'} {kind} {obj.name}", obj=obj, extra={"kind": kind, "action": action},
        )
        return Response({
            "message": "Emergency record updated",
            "record": serialize_emergency_record(kind or getattr(obj, "category", "hospital"), obj),
        })
