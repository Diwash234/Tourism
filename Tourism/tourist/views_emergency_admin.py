"""Admin emergency directory: add accurate local services to the DB and official CSVs."""
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.logging_services import log_action
from .community_data_service import (
    DuplicateEmergency,
    publish_official_emergency,
    serialize_emergency_record,
)
from .models import Hospital, InfrastructureSubmission, OSMEssentialService, PoliceStation
from .permissions import IsAdminOrStaff
from .views_admin import _require_capability


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

        hospitals = Hospital.objects.select_related("destination").order_by("-updated_at")
        police = PoliceStation.objects.select_related("destination").order_by("-updated_at")
        essentials = OSMEssentialService.objects.exclude(category__in=["hospital", "police"]).order_by("-updated_at")
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

        rows = []
        if kind in {"", "hospital"}:
            rows.extend(serialize_emergency_record("hospital", row) for row in hospitals[:80])
        if kind in {"", "police"}:
            rows.extend(serialize_emergency_record("police", row) for row in police[:80])
        if kind not in {"hospital", "police"}:
            qs = essentials.filter(category=kind) if kind else essentials
            for row in qs[:80]:
                if district:
                    tags = row.raw_tags or {}
                    hay = f"{row.address} {tags.get('district', '')} {tags.get('province', '')}"
                    if district.lower() not in hay.lower():
                        continue
                rows.append(serialize_emergency_record(row.category, row))

        pending = InfrastructureSubmission.objects.filter(
            status=InfrastructureSubmission.Status.PENDING,
            place_type__in=["hospital", "police", "pharmacy", "fire_station", "ambulance", "blood_bank", "clinic"],
        ).select_related("submitted_by").order_by("-created_at")[:50]

        return Response({
            "count": len(rows),
            "results": rows,
            "pending_submissions": [_submission_row(item) for item in pending],
            "coverage": {
                "hospitals": Hospital.objects.exclude(is_archived=True).count(),
                "police": PoliceStation.objects.exclude(is_archived=True).count(),
                "pharmacy": OSMEssentialService.objects.filter(category="pharmacy", is_archived=False).count(),
                "fire_station": OSMEssentialService.objects.filter(category="fire_station", is_archived=False).count(),
                "ambulance": OSMEssentialService.objects.filter(category="ambulance", is_archived=False).count(),
            },
            "notice": (
                "Add only accurate records with coordinates. This does not scrape Google or Facebook, "
                "and it does not invent pharmacies per ward. Existing OpenStreetMap sync still applies."
            ),
        })

    def post(self, request):
        _require_capability(request, "safety", "add")
        try:
            obj, csv_written = publish_official_emergency(request.data, request.user)
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
            message=f"Added {kind} {obj.name}", obj=obj, extra={"kind": kind, "csv_written": csv_written},
        )
        return Response({
            "id": obj.id,
            "message": "Saved to the emergency directory and appended to the official CSV when the row was new.",
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
        if action == "verify":
            obj.is_verified = True
            obj.verified_at = timezone.now()
        elif action == "archive":
            obj.is_archived = True
        elif action == "restore":
            obj.is_archived = False
        for field in ("name", "phone", "address", "opening_hours"):
            if field in request.data:
                setattr(obj, field, str(request.data.get(field) or "")[:300])
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
        obj.save()
        log_action(
            request, f"emergency.{action or 'update'}", category="admin",
            message=f"{action or 'Updated'} {kind} {obj.name}", obj=obj, extra={"kind": kind, "action": action},
        )
        return Response({
            "message": "Emergency record updated",
            "record": serialize_emergency_record(kind or getattr(obj, "category", "hospital"), obj),
        })
