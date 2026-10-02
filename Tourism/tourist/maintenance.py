"""
Maintenance mode middleware — returns 503 during maintenance windows.
"""
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Returns 503 Service Unavailable when MAINTENANCE_MODE is True.

    Set MAINTENANCE_MODE=true in the environment to enable.
    Health checks and admin access are always allowed.
    """

    def process_request(self, request):
        if not getattr(settings, "MAINTENANCE_MODE", False):
            return None

        # Allow health checks
        if request.path.startswith("/health") or request.path.startswith("/api/v1/health"):
            return None

        # Allow admin access
        if request.path.startswith("/admin"):
            return None

        # Allow static files
        if request.path.startswith("/static/") or request.path.startswith("/media/"):
            return None

        return JsonResponse(
            {
                "error": {
                    "code": "maintenance_mode",
                    "message": "The system is temporarily under maintenance. Please try again later.",
                    "details": {},
                }
            },
            status=503,
        )
