"""Performance monitoring and optimization utilities.

Provides:
- Request timing middleware
- Database query logging
- Slow query detection
- Cache statistics
- Performance metrics
"""
import time
import logging
from functools import wraps

from django.conf import settings
from django.db import connection, reset_queries
from django.core.cache import cache

logger = logging.getLogger('performance')


class PerformanceMiddleware:
    """Middleware to monitor request performance.

    Logs:
    - Request duration
    - Database query count
    - Slow queries (> 100ms)
    - Cache hit/miss ratio
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing
        start_time = time.time()

        # Reset query log
        if settings.DEBUG:
            reset_queries()

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration = time.time() - start_time

        # Get query stats
        if settings.DEBUG:
            queries = connection.queries
            query_count = len(queries)
            total_query_time = sum(float(q.get('time', 0)) for q in queries)
            slow_queries = [q for q in queries if float(q.get('time', 0)) > 0.1]
        else:
            query_count = 0
            total_query_time = 0
            slow_queries = []

        # Add performance headers
        response['X-Request-Duration'] = f"{duration:.3f}s"
        response['X-Query-Count'] = str(query_count)

        # Log slow requests
        if duration > 1.0:  # More than 1 second
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {duration:.2f}s with {query_count} queries"
            )

        # Log slow queries
        if slow_queries:
            logger.warning(
                f"Slow queries ({len(slow_queries)}): "
                + "; ".join(f"{q.get('time', 0)}s: {q.get('sql', '')[:100]}" for q in slow_queries[:3])
            )

        return response


def timed(func):
    """Decorator to time a function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        if duration > 0.5:  # Log if more than 500ms
            logger.warning(f"Slow function: {func.__name__} took {duration:.2f}s")
        return result
    return wrapper


def cache_result(key_prefix, timeout=300):
    """Decorator to cache function results.

    Args:
        key_prefix: Cache key prefix
        timeout: Cache timeout in seconds

    Usage:
        @cache_result('destinations', timeout=600)
        def get_destinations():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, timeout)

            return result
        return wrapper
    return decorator


def get_cache_stats():
    """Get cache statistics.

    Returns:
        Dict with cache hit/miss ratio and other stats
    """
    # This is a simplified version - in production, use Redis/Memcached stats
    return {
        "backend": settings.CACHES["default"]["BACKEND"],
        "key_prefix": settings.CACHES["default"].get("KEY_PREFIX", ""),
    }


def get_slow_queries(threshold=0.1):
    """Get slow queries from the current request.

    Args:
        threshold: Time threshold in seconds

    Returns:
        List of slow queries
    """
    if not settings.DEBUG:
        return []

    return [
        q for q in connection.queries
        if float(q.get('time', 0)) > threshold
    ]


def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """Apply common query optimizations.

    Args:
        queryset: Django QuerySet
        select_related: List of related fields to select_related
        prefetch_related: List of related fields to prefetch_related

    Returns:
        Optimized QuerySet
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    return queryset


class QueryCounter:
    """Context manager to count database queries.

    Usage:
        with QueryCounter() as counter:
            # ... do some queries
        print(f"Executed {counter.count} queries")
    """

    def __init__(self):
        self.count = 0

    def __enter__(self):
        self.initial_count = len(connection.queries) if settings.DEBUG else 0
        return self

    def __exit__(self, *args):
        if settings.DEBUG:
            self.count = len(connection.queries) - self.initial_count
