"""
system_health/checks.py
-----------------------
Live diagnostic checks: DB latency, disk usage, memory usage, ML service
reachability, Overpass/Wikimedia reachability, recent error rate. Each
check returns a dict with an `ok` boolean and a `value`/`latency_ms`/`note`.

Used by both:
  - `system_health.views.live_status` (public JSON endpoint the React
    dashboard pings every 10s)
  - `python manage.py health_snapshot` management command (cron-friendly
    writer into HealthSample for time-series graphing)
"""
from __future__ import annotations

import os
import shutil
import socket
import time
from typing import Any

import django
from django.conf import settings
from django.db import connection
from django.db.models import Count
from django.utils import timezone

# Only needed to populate samples
def _sample_model():
    from audit.models import ErrorEvent, HealthSample  # noqa: local import
    return ErrorEvent, HealthSample


def _db_check():
    start = time.monotonic()
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
            c.fetchone()
        latency = (time.monotonic() - start) * 1000
        return {"ok": latency < 500, "latency_ms": round(latency, 2)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _disk_check():
    try:
        usage = shutil.disk_usage(settings.BASE_DIR)
        pct = (usage.used / usage.total) * 100 if usage.total else 0
        return {
            "ok": pct < 95,
            "disk_used_pct": round(pct, 1),
            "free_bytes": usage.free,
            "total_bytes": usage.total,
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _memory_check():
    try:
        import psutil  # optional
        m = psutil.virtual_memory()
        return {"ok": m.percent < 90, "memory_used_pct": m.percent}
    except Exception:
        # psutil is optional; return neutral result if unavailable
        return {"ok": True, "memory_used_pct": None, "note": "psutil not installed"}


def _cpu_check():
    try:
        import psutil
        return {"ok": True, "cpu_pct": psutil.cpu_percent(interval=0.2)}
    except Exception:
        return {"ok": True, "cpu_pct": None, "note": "psutil not installed"}


def _port_check(host: str, port: int, timeout: float = 1.5) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"ok": True, "host": host, "port": port}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "host": host, "port": port, "error": str(e)[:200]}


def _http_check(url: str, timeout: float = 2.0) -> dict:
    try:
        import requests
        start = time.monotonic()
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "TourismHealthCheck/1.0"})
        latency = (time.monotonic() - start) * 1000
        return {"ok": r.status_code < 500, "status": r.status_code, "latency_ms": round(latency, 1)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _media_storage_check():
    media_root = getattr(settings, "MEDIA_ROOT", "")
    try:
        if not media_root or not os.path.isdir(str(media_root)):
            return {"ok": False, "note": "MEDIA_ROOT does not exist or is unset"}
        probe = os.path.join(str(media_root), ".health_write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _error_rate(window_minutes: int = 5) -> dict:
    ErrorEvent, _ = _sample_model()
    cutoff = timezone.now() - timezone.timedelta(minutes=window_minutes)
    recent = ErrorEvent.objects.filter(last_seen__gte=cutoff).count()
    # Very rough rate per minute
    rate = recent / window_minutes
    return {
        "ok": rate < 2,
        f"errors_last_{window_minutes}min": recent,
        "errors_per_minute": round(rate, 2),
    }


def _ml_check():
    # ML service typically runs on 8001 if started; otherwise optional
    ml_port = os.environ.get("ML_SERVICE_PORT", "8001")
    try:
        port = int(ml_port)
        r = _http_check(f"http://localhost:{port}/health", timeout=1.5)
        if not r.get("ok"):
            r = _port_check("localhost", port, timeout=1.0)
        return r
    except Exception:
        return {"ok": None, "note": "ML service not configured"}


def run_all_checks() -> dict[str, Any]:
    """Return the full live status dict the React diagnostics page uses."""
    db = _db_check()
    disk = _disk_check()
    mem = _memory_check()
    cpu = _cpu_check()
    media = _media_storage_check()
    errs = _error_rate(5)
    ml = _ml_check()
    overpass = _http_check("https://overpass-api.de/api/interpreter?data=%5Bout:json%5D;node(1);out;", timeout=3.0)
    wikimedia = _http_check("https://commons.wikimedia.org/w/api.php?action=query&meta=siteinfo&siprop=general&format=json", timeout=3.0)
    dhm = _http_check(settings.DHM_FEED_URL, timeout=3.0) if settings.DHM_FEED_URL else {"ok": True, "configured": False, "note": "DHM feed not configured"}
    bipad = _http_check(settings.BIPAD_FEED_URL, timeout=3.0) if settings.BIPAD_FEED_URL else {"ok": True, "configured": False, "note": "BIPAD feed not configured"}
    routing = _http_check(settings.ROUTING_API_URL, timeout=3.0) if settings.ROUTING_API_URL else {"ok": True, "configured": False, "note": "Road routing not configured"}

    overall_ok = db["ok"] and disk["ok"] and media["ok"]
    if errs.get("errors_per_minute", 0) > 10:
        overall_ok = False

    return {
        "ok": overall_ok,
        "checked_at": timezone.now().isoformat(),
        "checks": {
            "database": db,
            "disk": disk,
            "memory": mem,
            "cpu": cpu,
            "media_storage": media,
            "ml_service": ml,
            "overpass_api": overpass,
            "wikimedia_api": wikimedia,
            "dhm_feed": dhm,
            "bipad_feed": bipad,
            "routing_service": routing,
            "error_rate": errs,
        },
    }


def write_snapshot() -> object:
    """Write a HealthSample row from current checks. Returns the instance."""
    from audit.models import HealthSample  # local to avoid import order issues
    r = run_all_checks()
    c = r["checks"]
    sample = HealthSample.objects.create(
        source="django",
        db_ok=c["database"]["ok"],
        cache_ok=True,
        storage_ok=c["disk"]["ok"] and c["media_storage"]["ok"],
        ml_ok=c["ml_service"].get("ok"),
        overpass_ok=c["overpass_api"].get("ok"),
        media_storage_ok=c["media_storage"]["ok"],
        db_latency_ms=c["database"].get("latency_ms"),
        disk_used_pct=c["disk"].get("disk_used_pct"),
        memory_used_pct=c["memory"].get("memory_used_pct"),
        cpu_pct=c["cpu"].get("cpu_pct"),
        error_rate_5min=c["error_rate"].get("errors_per_minute"),
        notes="automatic snapshot" if r["ok"] else "degraded",
        extra={"checks": {k: v for k, v in c.items() if "error" not in v}},
    )
    return sample
