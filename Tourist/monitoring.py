"""Monitoring and alerting system.

Provides:
- API health monitoring
- Database health checks
- Cache health checks
- Alert management
- Performance metrics
"""
import logging
import time
from datetime import timedelta

from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def check_api_health():
    """Check API health.

    Returns:
        Dict with health status
    """
    try:
        start = time.time()

        # Check if API is responding
        from django.http import JsonResponse
        response = JsonResponse({"status": "ok"})

        duration = time.time() - start

        return {
            "status": "healthy",
            "response_time_ms": round(duration * 1000, 2),
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as exc:
        logger.error(f"API health check failed: {exc}")
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": timezone.now().isoformat(),
        }


def check_database_health():
    """Check database health.

    Returns:
        Dict with health status
    """
    try:
        start = time.time()

        # Check database connection
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()

        duration = time.time() - start

        # Get connection stats
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity")
            connections = cur.fetchone()[0]

        return {
            "status": "healthy",
            "response_time_ms": round(duration * 1000, 2),
            "vendor": connection.vendor,
            "connections": connections,
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": timezone.now().isoformat(),
        }


def check_cache_health():
    """Check cache health.

    Returns:
        Dict with health status
    """
    try:
        start = time.time()

        # Test cache
        test_key = "health_check_test"
        cache.set(test_key, "ok", 10)
        value = cache.get(test_key)
        cache.delete(test_key)

        duration = time.time() - start

        if value == "ok":
            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2),
                "backend": settings.CACHES["default"]["BACKEND"],
                "timestamp": timezone.now().isoformat(),
            }
        else:
            return {
                "status": "degraded",
                "error": "Cache read/write test failed",
                "timestamp": timezone.now().isoformat(),
            }

    except Exception as exc:
        logger.error(f"Cache health check failed: {exc}")
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": timezone.now().isoformat(),
        }


def check_disk_space():
    """Check disk space.

    Returns:
        Dict with disk usage
    """
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")

        return {
            "status": "healthy" if free > 1024**3 else "warning",  # 1GB threshold
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_percent": round(used / total * 100, 1),
        }

    except Exception as exc:
        logger.error(f"Disk space check failed: {exc}")
        return {
            "status": "unknown",
            "error": str(exc),
        }


def check_external_services():
    """Check external service health.

    Returns:
        Dict with service statuses
    """
    services = {}

    # Check ML service
    services['ml_service'] = _check_ml_service()

    # Check image server
    services['image_server'] = _check_image_server()

    return services


def get_system_metrics():
    """Get system metrics.

    Returns:
        Dict with system metrics
    """
    try:
        import psutil

        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": timezone.now().isoformat(),
        }

    except ImportError:
        return {
            "cpu_percent": None,
            "memory_percent": None,
            "disk_percent": None,
            "timestamp": timezone.now().isoformat(),
        }


def send_alert(message, severity="warning"):
    """Send an alert.

    Args:
        message: Alert message
        severity: Alert severity (info, warning, error, critical)
    """
    try:
        # Log the alert
        log_func = {
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical,
        }.get(severity, logger.warning)

        log_func(f"ALERT [{severity.upper()}]: {message}")

        # In production, send to Slack, PagerDuty, etc.
        # _send_slack_alert(message, severity)
        # _send_pagerduty_alert(message, severity)

    except Exception as exc:
        logger.error(f"Error sending alert: {exc}")


def run_health_checks():
    """Run all health checks.

    Returns:
        Dict with all health check results
    """
    results = {
        "api": check_api_health(),
        "database": check_database_health(),
        "cache": check_cache_health(),
        "disk": check_disk_space(),
        "external_services": check_external_services(),
        "system": get_system_metrics(),
    }

    # Determine overall status
    statuses = [
        results["api"]["status"],
        results["database"]["status"],
        results["cache"]["status"],
    ]

    if "unhealthy" in statuses:
        results["overall"] = "unhealthy"
    elif "degraded" in statuses or "warning" in statuses:
        results["overall"] = "degraded"
    else:
        results["overall"] = "healthy"

    # Send alerts for unhealthy services
    if results["overall"] == "unhealthy":
        send_alert("System health check failed", "critical")

    return results


def _check_ml_service():
    """Check ML service health."""
    try:
        import requests

        ml_url = settings.ML_SERVICE_URL
        response = requests.get(f"{ml_url}/health", timeout=5)

        if response.status_code == 200:
            return {"status": "healthy"}
        else:
            return {"status": "degraded", "status_code": response.status_code}

    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


def _check_image_server():
    """Check image server health."""
    try:
        import requests

        image_url = settings.IMAGE_BASE_URL
        if not image_url:
            return {"status": "not_configured"}

        response = requests.get(image_url, timeout=5)

        if response.status_code == 200:
            return {"status": "healthy"}
        else:
            return {"status": "degraded", "status_code": response.status_code}

    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}
