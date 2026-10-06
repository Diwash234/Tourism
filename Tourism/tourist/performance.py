"""
Performance optimization utilities.
"""
import logging
import threading
import time
import tracemalloc
from functools import wraps
from typing import Callable

from django.conf import settings
from django.core.cache import cache
from django.db import connection, reset_queries

logger = logging.getLogger(__name__)


def query_counter(func: Callable) -> Callable:
    """Decorator that logs the number of database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        query_count = len(connection.queries)
        logger.info(
            "%s executed %d queries in %.3fs",
            func.__name__,
            query_count,
            elapsed,
        )
        return result
    return wrapper


def cache_page(timeout: int = 300):
    """Decorator to cache a view's response."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            from django.http import HttpResponse

            cache_key = f"page:{request.path}:{request.META.get('QUERY_STRING', '')}"
            cached = cache.get(cache_key)
            if cached is not None:
                return HttpResponse(cached)

            response = func(request, *args, **kwargs)
            cache.set(cache_key, response.content, timeout=timeout)
            return response
        return wrapper
    return decorator


def select_related_fields(*fields: str):
    """Decorator to add select_related to a queryset."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            queryset = func(*args, **kwargs)
            if fields:
                queryset = queryset.select_related(*fields)
            return queryset
        return wrapper
    return decorator


def prefetch_related_fields(*fields: str):
    """Decorator to add prefetch_related to a queryset."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            queryset = func(*args, **kwargs)
            if fields:
                queryset = queryset.prefetch_related(*fields)
            return queryset
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Request performance monitoring
#
# settings.MIDDLEWARE lists 'tourist.performance.PerformanceMonitoringMiddleware'.
# Commit d1a59e9 rewrote this module and dropped the class while settings kept
# referencing it, so every request died with an ImportError while loading
# middleware. The class is restored below.
# ---------------------------------------------------------------------------

# Performance thresholds (in seconds)
SLOW_REQUEST_THRESHOLD = getattr(settings, "SLOW_REQUEST_THRESHOLD", 1.0)
SLOW_QUERY_THRESHOLD = getattr(settings, "SLOW_QUERY_THRESHOLD", 0.5)

# Aggregated stats live in the cache so they work across processes.
STATS_CACHE_KEY = "perf:stats"
STATS_CACHE_TTL = 300  # 5 minutes

# Thread-local storage for request timing
_thread_locals = threading.local()


class PerformanceMonitoringMiddleware:
    """
    Middleware that monitors request performance.

    Tracks:
    - Request duration
    - Number of database queries
    - Slow query detection
    - Memory usage (if enabled)
    - Endpoint response times

    Add to MIDDLEWARE in settings.py:
        'tourist.performance.PerformanceMonitoringMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enable_query_log = getattr(settings, "ENABLE_QUERY_LOG", False)
        self.track_memory = getattr(settings, "TRACK_MEMORY_USAGE", False)

    def __call__(self, request):
        # Start timing
        start_time = time.perf_counter()
        start_queries = len(connection.queries) if self.enable_query_log else 0

        # Start memory tracking if enabled
        if self.track_memory and not tracemalloc.is_tracing():
            tracemalloc.start()

        # Store start time in thread locals for access in views
        _thread_locals.request_start_time = start_time

        # Process the request
        response = self.get_response(request)

        # Calculate metrics
        duration = time.perf_counter() - start_time
        end_queries = len(connection.queries) if self.enable_query_log else 0
        query_count = end_queries - start_queries

        # Get memory usage
        memory_usage = None
        if self.track_memory and tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            memory_usage = {
                "current_mb": round(current / 1024 / 1024, 2),
                "peak_mb": round(peak / 1024 / 1024, 2),
            }

        # Build metrics
        metrics = {
            "path": request.path,
            "method": request.method,
            "duration_ms": round(duration * 1000, 2),
            "query_count": query_count,
            "status_code": response.status_code,
            "memory": memory_usage,
            "timestamp": time.time(),
        }

        # Add query details if logging is enabled
        if self.enable_query_log and query_count > 0:
            queries = connection.queries[start_queries:end_queries]
            metrics["queries"] = [
                {
                    "sql": q.get("sql", "")[:500],
                    "time": float(q.get("time", 0)),
                }
                for q in queries
            ]

            # Detect slow queries
            slow_queries = [
                q for q in queries
                if float(q.get("time", 0)) > SLOW_QUERY_THRESHOLD
            ]
            if slow_queries:
                metrics["slow_queries"] = len(slow_queries)
                logger.warning(
                    f"Slow queries detected for {request.path}: "
                    f"{len(slow_queries)} queries > {SLOW_QUERY_THRESHOLD}s"
                )

        # Log slow requests
        #
        # The OpenAPI document endpoints are exempt. They are rebuilt from
        # scratch whenever the project's Python sources change, which costs
        # 10-30s of CPU by design and is then cached (see
        # Tourism/schema_cache.py). Reporting that one-off build as a "slow
        # request" on every code save buried genuine regressions underneath it,
        # so it is logged at info level instead and kept out of the warning.
        is_schema_endpoint = request.path.rstrip("/").endswith(
            ("/models", "/schema")
        ) or "/models/" in request.path or "/schema/" in request.path

        if duration > SLOW_REQUEST_THRESHOLD:
            if is_schema_endpoint:
                logger.info(
                    f"OpenAPI document build: {request.method} {request.path} "
                    f"took {duration:.2f}s (cached for subsequent requests)"
                )
            else:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s with {query_count} queries"
                )

        # Store metrics
        self._store_metrics(metrics)

        # Add performance headers in debug mode
        if settings.DEBUG:
            response["X-Request-Duration-ms"] = str(round(duration * 1000, 2))
            response["X-Query-Count"] = str(query_count)

        return response

    def _store_metrics(self, metrics):
        """Store metrics in cache for aggregation."""
        try:
            # Get existing stats. Plain dicts only: the cache pickles values,
            # and a defaultdict holding a lambda (as this used to) makes every
            # request fail to store anything.
            stats = cache.get(STATS_CACHE_KEY)
            if stats is None:
                stats = {
                    "requests": [],
                    "total_requests": 0,
                    "slow_requests": 0,
                    "total_duration_ms": 0,
                    "total_queries": 0,
                    "endpoint_stats": {},
                }

            # Update stats
            stats["total_requests"] += 1
            stats["total_duration_ms"] += metrics["duration_ms"]
            stats["total_queries"] += metrics["query_count"]

            if metrics["duration_ms"] > SLOW_REQUEST_THRESHOLD * 1000:
                stats["slow_requests"] += 1

            # Per-endpoint stats
            endpoint_key = f"{metrics['method']} {metrics['path']}"
            ep_stats = stats["endpoint_stats"].get(endpoint_key)
            if ep_stats is None:
                ep_stats = {"count": 0, "total_duration_ms": 0, "durations": []}
                stats["endpoint_stats"][endpoint_key] = ep_stats
            ep_stats["count"] += 1
            ep_stats["total_duration_ms"] += metrics["duration_ms"]
            ep_stats["durations"].append(metrics["duration_ms"])

            # Keep only last 100 durations per endpoint for percentile calc
            if len(ep_stats["durations"]) > 100:
                ep_stats["durations"] = ep_stats["durations"][-100:]

            # Keep only last 1000 requests
            stats["requests"].append(metrics)
            if len(stats["requests"]) > 1000:
                stats["requests"] = stats["requests"][-1000:]

            cache.set(STATS_CACHE_KEY, stats, STATS_CACHE_TTL)
        except Exception as e:
            logger.error(f"Failed to store performance metrics: {e}")
