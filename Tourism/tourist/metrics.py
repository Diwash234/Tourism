"""
Metrics collection and monitoring utilities.
"""
import logging
import time
from typing import Any, Optional

from django.db import connection

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and reports application metrics.

    Usage:
        metrics = MetricsCollector()
        metrics.increment("api.requests")
        metrics.timing("api.response_time", 0.5)
        metrics.gauge("api.active_users", 42)
    """

    def __init__(self):
        self._metrics = {}

    def increment(self, name: str, value: int = 1, tags: Optional[dict] = None):
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        self._metrics[key] = self._metrics.get(key, 0) + value

    def timing(self, name: str, value: float, tags: Optional[dict] = None):
        """Record a timing metric."""
        key = self._make_key(name, tags)
        self._metrics[key] = value

    def gauge(self, name: str, value: float, tags: Optional[dict] = None):
        """Set a gauge metric."""
        key = self._make_key(name, tags)
        self._metrics[key] = value

    def get_metrics(self) -> dict:
        """Get all collected metrics."""
        return self._metrics.copy()

    def reset(self):
        """Reset all metrics."""
        self._metrics.clear()

    def _make_key(self, name: str, tags: Optional[dict]) -> str:
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}[{tag_str}]"
        return name


# Global metrics instance
metrics = MetricsCollector()


def track_api_call(func):
    """Decorator to track API call metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            status = "success"
            return result
        except Exception as exc:
            status = "error"
            raise
        finally:
            elapsed = time.time() - start
            metrics.timing("api.response_time", elapsed, {"status": status})
            metrics.increment("api.calls", 1, {"status": status})
    return wrapper


def get_system_metrics() -> dict:
    """Get current system metrics."""
    return {
        "database": {
            "connections": len(connection.queries) if hasattr(connection, "queries") else 0,
        },
        "cache": {
            "keys": len(metrics.get_metrics()),
        },
        "timestamp": time.time(),
    }
