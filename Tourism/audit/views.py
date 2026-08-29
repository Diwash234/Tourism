"""
audit/views.py
--------------
Admin-only API endpoints for:
  * Listing / searching audit logs
  * Listing / resolving / acknowledging errors
  * Receiving frontend errors (anonymous-safe, ratelimited)
  * Dashboard summary counts
"""
from __future__ import annotations

from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import ActionCategory, AuditLog, ErrorEvent, HealthSample, Severity, Source
from .serializers import (
    AuditLogSerializer, ErrorEventActionSerializer, ErrorEventSerializer,
    FrontendErrorSerializer, HealthSampleSerializer,
)
from .logging_services import log_error as record_error


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
class IsAdminUserOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated: return False
        if u.is_superuser or getattr(u,"role",None) in {"admin","super_admin","tourism_admin"}: return True
        try: return u.capability_profile.allows("audit", "view")
        except Exception: return False


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserOrStaff]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").all()
        params = self.request.query_params
        if params.get("severity"):
            qs = qs.filter(severity=params["severity"])
        if params.get("category"):
            qs = qs.filter(category=params["category"])
        if params.get("source"):
            qs = qs.filter(source=params["source"])
        if params.get("action"):
            qs = qs.filter(action__icontains=params["action"])
        if params.get("object_type"):
            qs = qs.filter(object_type=params["object_type"])
        if params.get("object_id"):
            qs = qs.filter(object_id=params["object_id"])
        if params.get("user_id"):
            qs = qs.filter(user_id=params["user_id"])
        if params.get("endpoint"):
            qs = qs.filter(endpoint__icontains=params["endpoint"])
        if params.get("since"):
            qs = qs.filter(timestamp__gte=params["since"])
        return qs

    @action(detail=False, url_path="summary")
    def summary(self, request):
        """Aggregate counts for the admin dashboard."""
        since = timezone.now() - timezone.timedelta(hours=24)
        recent = AuditLog.objects.filter(timestamp__gte=since)
        by_severity = dict(recent.values_list("severity").annotate(c=Count("id")).values_list("severity", "c"))
        by_category = dict(recent.values_list("category").annotate(c=Count("id")).values_list("category", "c"))
        errors_open = ErrorEvent.objects.filter(resolved=False).count()
        errors_critical = ErrorEvent.objects.filter(
            resolved=False, severity=Severity.CRITICAL
        ).count()
        last_24h_errors = ErrorEvent.objects.filter(
            last_seen__gte=since,
        ).count()
        return Response({
            "audit_24h": recent.count(),
            "audit_by_severity": by_severity,
            "audit_by_category": by_category,
            "errors_open": errors_open,
            "errors_critical": errors_critical,
            "errors_last_24h": last_24h_errors,
            "latest_health": self._latest_health(),
        })

    @staticmethod
    def _latest_health():
        h = HealthSample.objects.first()
        if not h:
            return None
        return HealthSampleSerializer(h).data


# ---------------------------------------------------------------------------
# Error events
# ---------------------------------------------------------------------------
class ErrorEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ErrorEventSerializer
    permission_classes = [IsAdminUserOrStaff]

    def get_queryset(self):
        qs = ErrorEvent.objects.select_related("user", "acknowledged_by").all()
        p = self.request.query_params
        if p.get("resolved") is not None:
            qs = qs.filter(resolved=p["resolved"].lower() in ("1", "true", "yes"))
        if p.get("severity"):
            qs = qs.filter(severity=p["severity"])
        if p.get("source"):
            qs = qs.filter(source=p["source"])
        if p.get("error_type"):
            qs = qs.filter(error_type__icontains=p["error_type"])
        if p.get("endpoint"):
            qs = qs.filter(endpoint__icontains=p["endpoint"])
        if p.get("component"):
            qs = qs.filter(component__icontains=p["component"])
        return qs

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        if not (request.user.is_superuser or request.user.role in {"admin","super_admin","tourism_admin"} or getattr(request.user,"capability_profile",None) and request.user.capability_profile.allows("audit","change")):
            return Response({"detail":"Missing audit.change capability"},status=403)
        err = self.get_object()
        ser = ErrorEventActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        err.resolved = ser.validated_data.get("resolved", True)
        err.resolution_note = ser.validated_data.get("resolution_note", "")
        err.acknowledged_by = request.user
        err.acknowledged_at = timezone.now()
        err.save()
        return Response(ErrorEventSerializer(err).data)

    @action(detail=False, methods=["post"], url_path="bulk-resolve")
    def bulk_resolve(self, request):
        if not (request.user.is_superuser or request.user.role in {"admin","super_admin","tourism_admin"} or getattr(request.user,"capability_profile",None) and request.user.capability_profile.allows("audit","change")):
            return Response({"detail":"Missing audit.change capability"},status=403)
        ids = request.data.get("ids") or []
        note = request.data.get("resolution_note", "")
        n, _ = ErrorEvent.objects.filter(id__in=ids).update(
            resolved=True,
            acknowledged_by=request.user,
            acknowledged_at=timezone.now(),
            resolution_note=note,
        )
        return Response({"resolved": n})


# ---------------------------------------------------------------------------
# Health samples
# ---------------------------------------------------------------------------
class HealthSampleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HealthSampleSerializer
    permission_classes = [IsAdminUserOrStaff]
    queryset = HealthSample.objects.all()[:200]

    @action(detail=False, url_path="latest")
    def latest(self, request):
        h = HealthSample.objects.first()
        if not h:
            return Response({"ok": True, "message": "No samples yet"},
                            status=status.HTTP_200_OK)
        return Response(HealthSampleSerializer(h).data)


# ---------------------------------------------------------------------------
# Frontend error reporting (anonymous-safe; used by the React ErrorBoundary)
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def report_frontend_error(request):
    ser = FrontendErrorSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    d = ser.validated_data
    record_error(
        request=request,
        source=Source.FRONTEND,
        severity=Severity.ERROR,
        error_type=d.get("name") or "FrontendError",
        error_message=d.get("message", ""),
        traceback_text=d.get("stack", ""),
        endpoint=d.get("route") or d.get("url") or "",
        component=d.get("component"),
        extra={
            "url": d.get("url"),
            "request_id": d.get("request_id"),
            **(d.get("extra") or {}),
        },
        merge_window_seconds=300,
    )
    return Response({"ok": True}, status=status.HTTP_202_ACCEPTED)
