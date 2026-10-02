"""
Comprehensive health check endpoint for monitoring and deployment verification.
"""
import logging
import time

from django.db import connection
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class DetailedHealthView(APIView):
    """
    GET /api/v1/health/detailed/

    Comprehensive health check including:
    - Database connectivity
    - Cache connectivity
    - Disk space
    - Response time
    """
    permission_classes = [AllowAny]

    def get(self, request):
        start_time = time.time()
        checks = {}
        overall_status = "healthy"

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = {"status": "ok", "response_time_ms": 0}
        except Exception as exc:
            checks["database"] = {"status": "error", "error": str(exc)}
            overall_status = "unhealthy"

        # Cache check
        try:
            cache.set("health_check", "ok", 10)
            cache_value = cache.get("health_check")
            checks["cache"] = {"status": "ok" if cache_value == "ok" else "error"}
        except Exception as exc:
            checks["cache"] = {"status": "error", "error": str(exc)}
            overall_status = "unhealthy"

        # Disk space check
        try:
            import shutil
            stat = shutil.disk_usage("/")
            free_gb = stat.free / (1024 ** 3)
            total_gb = stat.total / (1024 ** 3)
            checks["disk"] = {
                "status": "ok" if free_gb > 1 else "warning",
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round((1 - stat.free / stat.total) * 100, 1),
            }
            if free_gb < 1:
                overall_status = "degraded"
        except Exception as exc:
            checks["disk"] = {"status": "error", "error": str(exc)}

        # Response time
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return Response({
            "status": overall_status,
            "timestamp": time.time(),
            "response_time_ms": elapsed_ms,
            "checks": checks,
        }, status=status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE)
