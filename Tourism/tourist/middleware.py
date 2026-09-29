"""
Custom middleware for the Tourism API.
"""
import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(MiddlewareMixin):
    """Adds X-Response-Time header to all responses."""

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            elapsed = time.time() - request.start_time
            response["X-Response-Time"] = f"{elapsed:.3f}s"
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Adds security headers to all responses."""

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"
        return response


class CORSSecurityMiddleware(MiddlewareMixin):
    """Adds CORS headers for API responses."""

    def process_response(self, request, response):
        response["Access-Control-Expose-Headers"] = "X-Request-Id, X-Response-Time"
        return response
