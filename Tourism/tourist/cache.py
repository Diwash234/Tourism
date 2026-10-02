"""
Caching utilities for the Tourism platform.
"""
import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL = 300  # 5 minutes


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from function arguments."""
    key_parts = [prefix]
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    raw = ":".join(key_parts)
    # Hash long keys to stay within memcached's 250-char limit
    if len(raw) > 200:
        return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"
    return raw


def cached(ttl: int = DEFAULT_CACHE_TTL, key_prefix: str = ""):
    """
    Decorator that caches a function's return value.

    Usage:
        @cached(ttl=600, key_prefix="destinations")
        def get_destinations():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = generate_cache_key(key_prefix or func.__name__, *args, **kwargs)
            result = cache.get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=ttl)
            return result
        return wrapper
    return decorator


def cached_queryset(queryset, cache_key: str, ttl: int = DEFAULT_CACHE_TTL):
    """Cache a queryset's evaluated results."""
    result = cache.get(cache_key)
    if result is not None:
        return result
    result = list(queryset)
    cache.set(cache_key, result, timeout=ttl)
    return result


def invalidate_cache(key: str):
    """Invalidate a specific cache key."""
    cache.delete(key)


def invalidate_pattern(pattern: str):
    """Invalidate all cache keys matching a pattern (requires Redis)."""
    try:
        from django_redis import get_redis_connection
        redis = get_redis_connection("default")
        keys = redis.keys(f"*{pattern}*")
        if keys:
            redis.delete(*keys)
    except Exception:
        cache.clear()


def get_cache_stats() -> dict:
    """Get basic cache statistics."""
    try:
        from django_redis import get_redis_connection
        redis = get_redis_connection("default")
        info = redis.info()
        return {
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_keys": redis.dbsize(),
        }
    except Exception:
        return {"error": "Cache stats unavailable (not using Redis)"}
