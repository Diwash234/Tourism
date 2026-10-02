"""Cache management utilities.

Provides:
- Cache versioning
- Cache warming
- Cache invalidation patterns
- Cache statistics
"""
import hashlib
import json
import logging
from functools import wraps

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

CACHE_VERSION = "v2"


def make_key(*args, **kwargs):
    """Generate a cache key from arguments.

    Args:
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        Cache key string
    """
    key_parts = [CACHE_VERSION]

    for arg in args:
        key_parts.append(str(arg))

    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")

    raw = ":".join(key_parts)
    # Hash long keys
    if len(raw) > 200:
        return f"{CACHE_VERSION}:{hashlib.md5(raw.encode()).hexdigest()}"
    return raw


def cached(timeout=300, key_prefix="cache"):
    """Decorator to cache function results.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key

    Usage:
        @cached(timeout=600, key_prefix="destinations")
        def get_destinations():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = make_key(key_prefix, func.__name__, *args, **kwargs)

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        wrapper.invalidate = lambda *a, **kw: cache.delete(
            make_key(key_prefix, func.__name__, *a, **kw)
        )
        wrapper.invalidate_all = lambda: cache.delete_pattern(f"{key_prefix}:{func.__name__}:*")

        return wrapper
    return decorator


def invalidate_pattern(pattern):
    """Invalidate all cache keys matching a pattern.

    Args:
        pattern: Pattern to match (e.g., "destinations:*")
    """
    # Note: This requires Redis backend. For other backends, this is a no-op.
    try:
        cache.delete_pattern(pattern)
    except AttributeError:
        logger.warning("Cache backend does not support delete_pattern")


def warm_cache(key, data, timeout=300):
    """Pre-populate cache with data.

    Args:
        key: Cache key
        data: Data to cache
        timeout: Cache timeout in seconds
    """
    cache.set(key, data, timeout)


def get_cache_stats():
    """Get cache statistics.

    Returns:
        Dict with cache statistics
    """
    # This is a simplified version. In production, use Redis/Memcached stats.
    return {
        "backend": settings.CACHES["default"]["BACKEND"],
        "version": CACHE_VERSION,
    }


class CacheManager:
    """Manager for cache operations."""

    @staticmethod
    def get(key, default=None):
        """Get value from cache."""
        return cache.get(key, default)

    @staticmethod
    def set(key, value, timeout=300):
        """Set value in cache."""
        cache.set(key, value, timeout)

    @staticmethod
    def delete(key):
        """Delete value from cache."""
        cache.delete(key)

    @staticmethod
    def clear():
        """Clear all cache."""
        cache.clear()

    @staticmethod
    def get_or_set(key, default, timeout=300):
        """Get value from cache or set it if not present."""
        value = cache.get(key)
        if value is None:
            value = default() if callable(default) else default
            cache.set(key, value, timeout)
        return value

    @staticmethod
    def increment(key, delta=1):
        """Increment a counter in cache."""
        try:
            return cache.incr(key, delta)
        except ValueError:
            cache.set(key, delta)
            return delta

    @staticmethod
    def decrement(key, delta=1):
        """Decrement a counter in cache."""
        try:
            return cache.decr(key, delta)
        except ValueError:
            cache.set(key, -delta)
            return -delta


# Cache key builders for common patterns
class CacheKeys:
    """Cache key builders for common patterns."""

    @staticmethod
    def public_config(language="en"):
        return make_key("public_config", language)

    @staticmethod
    def destination_detail(slug):
        return make_key("destination", slug)

    @staticmethod
    def destination_list(filters=None):
        return make_key("destinations", filters or {})

    @staticmethod
    def nearby_destinations(lat, lon, radius):
        return make_key("nearby", lat, lon, radius)

    @staticmethod
    def weather(lat, lon):
        return make_key("weather", lat, lon)

    @staticmethod
    def admin_stats():
        return make_key("admin_stats")

    @staticmethod
    def user_profile(user_id):
        return make_key("user_profile", user_id)

    @staticmethod
    def search_results(query, filters=None):
        return make_key("search", query, filters or {})
