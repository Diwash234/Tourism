"""Admin emergency directory: add accurate local services to the DB and official CSVs."""
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from .community_data_service import publish_official_emergency, serialize_emergency_record
from .models import Hospital, OSMEssentialService, PoliceStation
from .permissions import IsAdminOrStaff
from .views_admin import _require_capability


class AdminEmergencyDirectoryView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "safety", "view")
        q = (request.query_params.get("q") or "").strip()
        district = (request.query_params.get("district") or "").strip()
        kind = (request.query_params.get("kind") or "").strip().lower()
        if kind == "fire":
            kind = "fire_station"

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

        return Response({
            "count": len(rows),
            "results": rows,
            "coverage": {
                "hospitals": Hospital.objects.count(),
                "police": PoliceStation.objects.count(),
                "pharmacy": OSMEssentialService.objects.filter(category="pharmacy").count(),
                "fire_station": OSMEssentialService.objects.filter(category="fire_station").count(),
                "ambulance": OSMEssentialService.objects.filter(category="ambulance").count(),
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
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        kind = str(request.data.get("kind") or "").strip().lower()
        if kind == "fire":
            kind = "fire_station"
        return Response({
            "id": obj.id,
            "message": "Saved to the emergency directory and appended to the official CSV when the row was new.",
            "record": serialize_emergency_record(kind or getattr(obj, "category", "hospital"), obj),
            "csv_written": csv_written,
        }, status=201)
