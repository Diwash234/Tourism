"""
Custom middleware for the Tourism API.
"""
import ipaddress
import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

from .utils import geoip_lookup, get_client_ip

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


def _is_public_ip(ip_address):
    """True only for globally routable addresses.

    Private, loopback and link-local clients never get a lookup: their address
    must not be shipped to the GeoIP provider.
    """
    if not ip_address:
        return False
    try:
        return ipaddress.ip_address(ip_address).is_global
    except ValueError:
        return False


class _LazyGeoLocation:
    """Resolves the client location on first access rather than in the request.

    Middleware runs on every /api/ call, so looking up there would either block
    the response on an external HTTP call or send the visitor's IP to the
    provider for requests that never read the location. A view that does read
    ``request.geo_location`` triggers the cached, non-blocking lookup once.
    """

    __slots__ = ("_ip_address", "_resolved", "_value")

    def __init__(self, ip_address):
        self._ip_address = ip_address
        self._resolved = False
        self._value = None

    def _resolve(self):
        if not self._resolved:
            self._value = geoip_lookup(self._ip_address, blocking=False)
            self._resolved = True
        return self._value

    def __bool__(self):
        return bool(self._resolve())

    def get(self, key, default=None):
        value = self._resolve()
        return value.get(key, default) if isinstance(value, dict) else default

    def __getitem__(self, key):
        value = self._resolve()
        if not isinstance(value, dict):
            raise KeyError(key)
        return value[key]

    def __repr__(self):
        if not self._resolved:
            return f"<unresolved geo location for {self._ip_address}>"
        return repr(self._value)


class GeoIPMiddleware:
    """
    Attaches `request.geo_location` (country/city/lat/lon or None) based on
    the client's IP address. This is used as a fallback whenever the
    frontend does not supply browser GPS coordinates. Lookups are lazy and
    best-effort; failures never break the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.geo_location = None
        if request.path.startswith("/api/"):
            ip_address = get_client_ip(request)
            if _is_public_ip(ip_address):
                request.geo_location = _LazyGeoLocation(ip_address)
        return self.get_response(request)
