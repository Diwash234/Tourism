"""
Advanced throttling classes for DRF.
"""
import logging
import time

from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class UserRateThrottle(SimpleRateThrottle):
    """Rate throttle per authenticated user."""
    scope = "user"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AnonRateThrottle(SimpleRateThrottle):
    """Rate throttle for anonymous users."""
    scope = "anon"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class BurstRateThrottle(SimpleRateThrottle):
    """Allows bursts of requests up to a limit."""
    scope = "burst"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SustainedRateThrottle(SimpleRateThrottle):
    """Sustained rate limit over a longer period."""
    scope = "sustained"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class EndpointRateThrottle(SimpleRateThrottle):
    """Per-endpoint rate limiting."""
    scope = "endpoint"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        endpoint = request.path
        return self.cache_format % {"scope": self.scope, "ident": f"{ident}:{endpoint}"}
