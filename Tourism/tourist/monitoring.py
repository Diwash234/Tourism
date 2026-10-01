"""
Monitoring and alerting utilities for the Tourism API.
"""
import logging
import time
from datetime import timedelta

from django.core.cache import cache
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Monitors system health and performance.
    """

    @staticmethod
    def get_system_stats():
        """Get current system statistics."""
        stats = {
            "timestamp": timezone.now().isoformat(),
            "database": SystemMonitor._get_db_stats(),
            "cache": SystemMonitor._get_cache_stats(),
            "memory": SystemMonitor._get_memory_stats(),
        }
        return stats

    @staticmethod
    def _get_db_stats():
        """Get database statistics."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity")
                connections = cursor.fetchone()[0]
            return {
                "status": "ok",
                "connections": connections,
            }
        except Exception as exc:
            logger.error(f"Database stats error: {exc}")
            return {"status": "error", "error": str(exc)}

    @staticmethod
    def _get_cache_stats():
        """Get cache statistics."""
        try:
            # This would need to be adapted based on the cache backend
            return {"status": "ok"}
        except Exception as exc:
            logger.error(f"Cache stats error: {exc}")
            return {"status": "error", "error": str(exc)}

    @staticmethod
    def _get_memory_stats():
        """Get memory statistics."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "status": "ok",
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            }
        except ImportError:
            return {"status": "unavailable", "error": "psutil not installed"}
        except Exception as exc:
            logger.error(f"Memory stats error: {exc}")
            return {"status": "error", "error": str(exc)}

    @staticmethod
    def check_health():
        """Perform a health check."""
        checks = {
            "database": SystemMonitor._check_database(),
            "cache": SystemMonitor._check_cache(),
        }
        all_healthy = all(check.get("status") == "ok" for check in checks.values())
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
        }

    @staticmethod
    def _check_database():
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {"status": "ok"}
        except Exception as exc:
            logger.error(f"Database health check failed: {exc}")
            return {"status": "error", "error": str(exc)}

    @staticmethod
    def _check_cache():
        """Check cache connectivity."""
        try:
            cache.set("health_check", "ok", 10)
            if cache.get("health_check") == "ok":
                return {"status": "ok"}
            return {"status": "error", "error": "Cache read/write failed"}
        except Exception as exc:
            logger.error(f"Cache health check failed: {exc}")
            return {"status": "error", "error": str(exc)}


class PerformanceMonitor:
    """
    Monitors API performance.
    """

    @staticmethod
    def track_request_time(view_name):
        """Track request processing time."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                PerformanceMonitor._record_metric(view_name, elapsed)
                return result
            return wrapper
        return decorator

    @staticmethod
    def _record_metric(view_name, elapsed):
        """Record a performance metric."""
        key = f"perf:{view_name}"
        metrics = cache.get(key, [])
        metrics.append({
            "timestamp": timezone.now().isoformat(),
            "elapsed": elapsed,
        })
        # Keep only the last 1000 metrics
        metrics = metrics[-1000:]
        cache.set(key, metrics, timeout=3600)

    @staticmethod
    def get_average_response_time(view_name, minutes=5):
        """Get average response time for a view."""
        key = f"perf:{view_name}"
        metrics = cache.get(key, [])
        cutoff = timezone.now() - timedelta(minutes=minutes)
        recent = [m for m in metrics if timezone.datetime.fromisoformat(m["timestamp"]) > cutoff]
        if not recent:
            return 0
        return sum(m["elapsed"] for m in recent) / len(recent)


class AlertManager:
    """
    Manages system alerts.
    """

    @staticmethod
    def send_alert(level, message, details=None):
        """Send an alert."""
        alert = {
            "level": level,
            "message": message,
            "details": details or {},
            "timestamp": timezone.now().isoformat(),
        }
        logger.warning(f"ALERT [{level}]: {message}")
        # In production, this would send to an alerting system
        cache.set(f"alert:{int(time.time())}", alert, timeout=86400)

    @staticmethod
    def check_thresholds():
        """Check system thresholds and send alerts if needed."""
        # Check database connections
        db_stats = SystemMonitor._get_db_stats()
        if db_stats.get("connections", 0) > 100:
            AlertManager.send_alert(
                "warning",
                "High database connection count",
                {"connections": db_stats["connections"]}
            )

        # Check memory usage
        memory_stats = SystemMonitor._get_memory_stats()
        if memory_stats.get("percent", 0) > 90:
            AlertManager.send_alert(
                "critical",
                "High memory usage",
                {"percent": memory_stats["percent"]}
            )
