"""
Advanced throttling classes for the Tourism API.
"""
import logging
import time

from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class UserRateThrottle(SimpleRateThrottle):
    """
    Rate throttle per authenticated user.
    """
    scope = "user"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AnonRateThrottle(SimpleRateThrottle):
    """
    Rate throttle for anonymous users.
    """
    scope = "anon"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class BurstRateThrottle(SimpleRateThrottle):
    """
    Allows bursts of requests up to a limit.
    """
    scope = "burst"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SustainedRateThrottle(SimpleRateThrottle):
    """
    Sustained rate limit over a longer period.
    """
    scope = "sustained"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class EndpointRateThrottle(SimpleRateThrottle):
    """
    Per-endpoint rate limiting.
    """
    scope = "endpoint"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        endpoint = request.path
        return self.cache_format % {"scope": self.scope, "ident": f"{ident}:{endpoint}"}


class IPRateThrottle(SimpleRateThrottle):
    """
    Rate limit per IP address.
    """
    scope = "ip"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class CustomRateThrottle(SimpleRateThrottle):
    """
    Custom rate throttle with dynamic rates based on user role.
    """
    scope = "custom"

    def get_rate(self):
        # Override this method to provide dynamic rates
        return super().get_rate()

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def allow_request(self, request, view):
        # Custom logic for allowing requests
        return super().allow_request(request, view)


class RoleBasedRateThrottle(SimpleRateThrottle):
    """
    Rate limit based on user role.
    """
    scope = "role"

    ROLE_RATES = {
        "tourist": "100/hour",
        "staff": "500/hour",
        "admin": "1000/hour",
    }

    def get_rate(self):
        # This would need access to the request to determine the role
        return super().get_rate()

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
