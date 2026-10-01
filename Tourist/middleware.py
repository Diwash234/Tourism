"""
Custom middleware for the Tourism platform.
"""
import logging
import time
import uuid

from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(MiddlewareMixin):
    """Adds X-Response-Time header to all responses."""

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            elapsed = time.time() - request.start_time
            response['X-Response-Time'] = f"{elapsed:.3f}s"
        return response


class RequestIdMiddleware(MiddlewareMixin):
    """Adds unique request ID for tracing."""

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())[:12]

    def process_response(self, request, response):
        if hasattr(request, 'request_id'):
            response['X-Request-Id'] = request.request_id
        return response


class CacheMiddleware(MiddlewareMixin):
    """Simple cache middleware for GET requests."""

    CACHE_TIMEOUT = 300  # 5 minutes

    def process_response(self, request, response):
        if request.method == 'GET' and response.status_code == 200:
            cache_key = f"cache:{request.path}"
            cached = cache.get(cache_key)
            if cached is None:
                cache.set(cache_key, response, timeout=self.CACHE_TIMEOUT)
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Adds security headers to all responses."""

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=()'
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware."""

    RATE_LIMIT = 100  # requests per window
    WINDOW = 60  # seconds

    def process_request(self, request):
        ip = self._get_client_ip(request)
        key = f"rate_limit:{ip}"

        requests = cache.get(key, [])
        now = time.time()

        # Remove old requests
        requests = [r for r in requests if r > now - self.WINDOW]

        if len(requests) >= self.RATE_LIMIT:
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Rate limit exceeded'},
                status=429
            )

        requests.append(now)
        cache.set(key, requests, timeout=self.WINDOW)
        return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
