"""
Rate limiting utilities and monitoring.
"""
import logging
import time
from functools import wraps
from typing import Callable

from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def custom_rate_limit(requests: int = 60, window: int = 60):
    """
    Decorator for custom rate limiting on API endpoints.

    Args:
        requests: Maximum number of requests allowed
        window: Time window in seconds

    Usage:
        @custom_rate_limit(requests=30, window=60)
        def my_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Generate unique key for this user/endpoint
            user_id = request.user.id if request.user.is_authenticated else request.META.get("REMOTE_ADDR", "anonymous")
            key = f"rate_limit:{func.__name__}:{user_id}"

            # Get current count
            now = time.time()
            window_start = now - window

            # Get request timestamps from cache
            timestamps = cache.get(key, [])
            # Remove old timestamps
            timestamps = [t for t in timestamps if t > window_start]

            if len(timestamps) >= requests:
                logger.warning("Rate limit exceeded for %s on %s", user_id, func.__name__)
                return Response(
                    {
                        "error": {
                            "code": "rate_limit_exceeded",
                            "message": f"Rate limit exceeded. Maximum {requests} requests per {window} seconds.",
                            "details": {"retry_after": int(window - (now - timestamps[0])) if timestamps else window},
                        }
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Add current request timestamp
            timestamps.append(now)
            cache.set(key, timestamps, timeout=window)

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def get_rate_limit_status(user_id: str, endpoint: str) -> dict:
    """Get the current rate limit status for a user/endpoint."""
    key = f"rate_limit:{endpoint}:{user_id}"
    timestamps = cache.get(key, [])
    now = time.time()
    # Clean old timestamps
    timestamps = [t for t in timestamps if t > now - 60]
    return {
        "remaining": max(0, 60 - len(timestamps)),
        "used": len(timestamps),
        "reset_at": int(timestamps[0] + 60) if timestamps else int(now + 60),
    }
