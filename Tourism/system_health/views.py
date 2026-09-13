"""
system_health/views.py
----------------------
Two endpoints:
  * GET  /api/v1/system/health        – anonymous-safe quick liveness probe
  * GET  /api/v1/system/health/full   – admin-only detailed check of every subsystem
  * GET  /api/v1/system/health/sample – admin-only; writes a HealthSample row
                                        and returns it (for "Run diagnostics now")
"""
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .checks import run_all_checks, write_snapshot


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def quick_health(_request):
    """Liveness probe used by Docker, uptime monitors, and the frontend
    top bar connectivity dot."""
    r = run_all_checks()
    return Response({
        "ok": r["ok"],
        "checked_at": r["checked_at"],
        "database_ok": r["checks"]["database"]["ok"],
        "disk_ok": r["checks"]["disk"]["ok"],
        "error_rate": r["checks"]["error_rate"].get("errors_per_minute", 0),
    })


@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def full_health(_request):
    return Response(run_all_checks())


@api_view(["POST", "GET"])
@permission_classes([permissions.IsAdminUser])
def sample_now(_request):
    sample = write_snapshot()
    return Response({
        "ok": sample.overall() != "critical",
        "sample": {
            "id": sample.pk,
            "timestamp": sample.timestamp.isoformat(),
            "overall": sample.overall(),
            "db_ok": sample.db_ok,
            "cache_ok": sample.cache_ok,
            "storage_ok": sample.storage_ok,
            "ml_ok": sample.ml_ok,
            "overpass_ok": sample.overpass_ok,
            "db_latency_ms": sample.db_latency_ms,
            "disk_used_pct": sample.disk_used_pct,
            "memory_used_pct": sample.memory_used_pct,
            "cpu_pct": sample.cpu_pct,
            "error_rate_5min": sample.error_rate_5min,
        },
    }, status=status.HTTP_200_OK)
