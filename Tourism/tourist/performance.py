"""
Performance Monitoring Module.

Provides:
- Request timing middleware
- Database query logging
- Slow query detection
- Memory usage tracking
- Endpoint response time percentiles

Usage:
    # Add to MIDDLEWARE in settings.py:
    'tourist.performance.PerformanceMonitoringMiddleware',

    # View stats:
    from tourist.performance import get_performance_stats
    stats = get_performance_stats()
"""

import logging
import threading
import time
import tracemalloc
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import connection, reset_queries

logger = logging.getLogger(__name__)

# Performance thresholds (in seconds)
SLOW_REQUEST_THRESHOLD = getattr(settings, "SLOW_REQUEST_THRESHOLD", 1.0)
SLOW_QUERY_THRESHOLD = getattr(settings, "SLOW_QUERY_THRESHOLD", 0.5)

# In-memory stats storage (use cache for multi-process)
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
        if duration > SLOW_REQUEST_THRESHOLD:
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
            # Get existing stats
            stats = cache.get(STATS_CACHE_KEY) or {
                "requests": [],
                "total_requests": 0,
                "slow_requests": 0,
                "total_duration_ms": 0,
                "total_queries": 0,
                "endpoint_stats": defaultdict(lambda: {
                    "count": 0,
                    "total_duration_ms": 0,
                    "durations": [],
                }),
            }

            # Update stats
            stats["total_requests"] += 1
            stats["total_duration_ms"] += metrics["duration_ms"]
            stats["total_queries"] += metrics["query_count"]

            if metrics["duration_ms"] > SLOW_REQUEST_THRESHOLD * 1000:
                stats["slow_requests"] += 1

            # Per-endpoint stats
            endpoint_key = f"{metrics['method']} {metrics['path']}"
            ep_stats = stats["endpoint_stats"][endpoint_key]
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


# ---------------------------------------------------------------------------
# Performance Statistics Functions
# ---------------------------------------------------------------------------

def get_performance_stats():
    """
    Get aggregated performance statistics.

    Returns:
        dict with:
        - total_requests: total requests tracked
        - slow_requests: number of slow requests
        - avg_response_time_ms: average response time
        - p50_response_time_ms: 50th percentile response time
        - p95_response_time_ms: 95th percentile response time
        - p99_response_time_ms: 99th percentile response time
        - avg_queries_per_request: average DB queries per request
        - endpoint_breakdown: per-endpoint statistics
    """
    stats = cache.get(STATS_CACHE_KEY)
    if not stats:
        return {
            "total_requests": 0,
            "slow_requests": 0,
            "avg_response_time_ms": 0,
            "p50_response_time_ms": 0,
            "p95_response_time_ms": 0,
            "p99_response_time_ms": 0,
            "avg_queries_per_request": 0,
            "endpoint_breakdown": {},
        }

    total = stats["total_requests"]
    if total == 0:
        return {
            "total_requests": 0,
            "slow_requests": 0,
            "avg_response_time_ms": 0,
            "p50_response_time_ms": 0,
            "p95_response_time_ms": 0,
            "p99_response_time_ms": 0,
            "avg_queries_per_request": 0,
            "endpoint_breakdown": {},
        }

    # Calculate percentiles from all request durations
    all_durations = []
    for req in stats["requests"]:
        all_durations.append(req["duration_ms"])

    all_durations.sort()

    def percentile(data, p):
        """Calculate the p-th percentile."""
        if not data:
            return 0
        k = (len(data) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f])

    # Endpoint breakdown
    endpoint_breakdown = {}
    for endpoint, ep_stats in stats["endpoint_stats"].items():
        durations = sorted(ep_stats["durations"])
        endpoint_breakdown[endpoint] = {
            "count": ep_stats["count"],
            "avg_duration_ms": round(ep_stats["total_duration_ms"] / max(ep_stats["count"], 1), 2),
            "p50_duration_ms": round(percentile(durations, 50), 2),
            "p95_duration_ms": round(percentile(durations, 95), 2),
        }

    return {
        "total_requests": total,
        "slow_requests": stats["slow_requests"],
        "avg_response_time_ms": round(stats["total_duration_ms"] / total, 2),
        "p50_response_time_ms": round(percentile(all_durations, 50), 2),
        "p95_response_time_ms": round(percentile(all_durations, 95), 2),
        "p99_response_time_ms": round(percentile(all_durations, 99), 2),
        "avg_queries_per_request": round(stats["total_queries"] / total, 2),
        "endpoint_breakdown": endpoint_breakdown,
    }


def get_slow_endpoints(threshold_ms=1000, limit=10):
    """
    Get the slowest endpoints.

    Args:
        threshold_ms: Minimum response time to be considered slow.
        limit: Maximum number of endpoints to return.

    Returns:
        List of dicts with endpoint, count, and avg_duration_ms.
    """
    stats = get_performance_stats()
    slow = [
        {"endpoint": ep, **data}
        for ep, data in stats["endpoint_breakdown"].items()
        if data["avg_duration_ms"] >= threshold_ms
    ]
    slow.sort(key=lambda x: x["avg_duration_ms"], reverse=True)
    return slow[:limit]


def reset_performance_stats():
    """Reset all performance statistics."""
    cache.delete(STATS_CACHE_KEY)
    logger.info("Performance statistics reset")


# ---------------------------------------------------------------------------
# Database Query Utilities
# ---------------------------------------------------------------------------

def get_query_stats():
    """
    Get database query statistics for the current request.

    Returns:
        dict with query count, total time, and slow queries.
    """
    queries = connection.queries
    if not queries:
        return {"count": 0, "total_time_ms": 0, "slow_queries": []}

    total_time = sum(float(q.get("time", 0)) for q in queries)
    slow = [
        {"sql": q.get("sql", "")[:200], "time_ms": round(float(q.get("time", 0)) * 1000, 2)}
        for q in queries
        if float(q.get("time", 0)) > SLOW_QUERY_THRESHOLD
    ]

    return {
        "count": len(queries),
        "total_time_ms": round(total_time * 1000, 2),
        "slow_queries": slow,
    }


# ---------------------------------------------------------------------------
# Memory Usage Utilities
# ---------------------------------------------------------------------------

def get_memory_usage():
    """
    Get current memory usage of the process.

    Returns:
        dict with current and peak memory in MB, or None if tracking is disabled.
    """
    if not tracemalloc.is_tracing():
        return None

    current, peak = tracemalloc.get_traced_memory()
    return {
        "current_mb": round(current / 1024 / 1024, 2),
        "peak_mb": round(peak / 1024 / 1024, 2),
    }


def start_memory_tracking():
    """Start memory tracking with tracemalloc."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()


def stop_memory_tracking():
    """Stop memory tracking."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()


# ---------------------------------------------------------------------------
# Decorator for view-level performance monitoring
# ---------------------------------------------------------------------------

def monitor_performance(func):
    """
    Decorator to monitor the performance of a specific view or function.

    Usage:
        @monitor_performance
        def my_view(request):
            ...
    """
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start

        if duration > SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow function: {func.__name__} took {duration:.2f}s"
            )

        return result

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
