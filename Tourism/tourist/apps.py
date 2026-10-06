from django.apps import AppConfig


def _harden_sqlite_connection(sender, connection, **kwargs):
    """Make file-backed SQLite production-viable on every new connection.

    WAL gives concurrent readers + one writer (the honest SQLite ceiling),
    synchronous=NORMAL keeps WAL durable across app crashes, foreign_keys
    enforces referential integrity (SQLite ships with it OFF), and
    busy_timeout absorbs brief write-lock contention. Never fatal: if a
    pragma cannot run (e.g. read-only media) the app still starts.
    """
    if getattr(connection, "vendor", "") != "sqlite":
        return
    try:
        with connection.cursor() as cur:
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute("PRAGMA foreign_keys=ON;")
            cur.execute("PRAGMA busy_timeout=5000;")
    except Exception:  # pragma: no cover - defensive, must never block startup
        pass


class TouristsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tourist"
    verbose_name = "Tourism Portal"

    def ready(self):
        import tourist.signals  # noqa: F401

        from django.db.backends.signals import connection_created

        connection_created.connect(_harden_sqlite_connection)
        _start_notification_worker()
        _warm_openapi_schema()


def _warm_openapi_schema():
    """Build the OpenAPI document off the request path when enabled.

    Registering ~1,600 URL patterns and walking every view to produce the
    document costs 10-30s of CPU. That cost is paid once per code change
    (the cache is fingerprinted against the project's .py sources), which is
    useful in production to spare the first schema request. Local DEBUG runs
    disable this by default so startup work does not compete with the website.

    Warming it in a daemon thread means the document is usually ready before
    anyone asks for it. Never fatal, skipped under management commands and
    tests, and disabled with OPENAPI_SCHEMA_WARMUP_ENABLED=0 on
    memory-constrained instances (the transient allocation is what pushed
    Render's 512 MiB plan over its limit).
    """
    import os
    import sys
    import threading

    from django.conf import settings

    if not getattr(settings, "OPENAPI_SCHEMA_WARMUP_ENABLED", True):
        return
    argv = " ".join(sys.argv)
    serving = any(k in argv for k in ("runserver", "gunicorn", "uvicorn", "daphne", "waitress"))
    if not serving or "test" in sys.argv or "migrate" in sys.argv:
        return
    # runserver's autoreloader spawns a child; only the child should warm.
    if "runserver" in argv and "--noreload" not in argv and os.environ.get("RUN_MAIN") != "true":
        return

    def warm():
        import logging
        import time

        from django.db import close_old_connections

        log = logging.getLogger("tourist.schema_cache")
        time.sleep(2)  # let the server finish binding
        try:
            from Tourism.schema_cache import warm_schema_cache

            started = time.monotonic()
            if warm_schema_cache():
                log.info("OpenAPI schema warmed in %.1fs", time.monotonic() - started)
            else:
                log.warning("OpenAPI schema warm-up produced no document")
        except Exception as exc:  # noqa: BLE001 - warmup must never kill startup
            log.warning("OpenAPI schema warm-up skipped: %s", exc)
        finally:
            close_old_connections()

    threading.Thread(target=warm, name="openapi-schema-warmup", daemon=True).start()


def _start_notification_worker():
    """Deliver queued/failed email, SMS and push notifications automatically.

    Notifications are queued in the DB with bounded retries; without a
    processor those rows sat as "queued" forever unless an operator ran
    `manage.py process_notification_queue` by cron. This daemon thread runs
    the same processor every NOTIFICATION_WORKER_INTERVAL seconds inside the
    web process (opt out with NOTIFICATION_WORKER_ENABLED=0 when a cron or
    dedicated worker owns delivery). Skipped under management commands and
    tests so they stay deterministic.
    """
    import os
    import sys
    import threading
    import time

    from django.conf import settings

    if not getattr(settings, "NOTIFICATION_WORKER_ENABLED", True):
        return
    argv = " ".join(sys.argv)
    serving = any(k in argv for k in ("runserver", "gunicorn", "uvicorn", "daphne", "waitress"))
    if not serving or "test" in sys.argv:
        return
    # runserver's autoreloader spawns a child; only the child should run it.
    if "runserver" in argv and "--noreload" not in argv and os.environ.get("RUN_MAIN") != "true":
        return
    interval = max(15, int(getattr(settings, "NOTIFICATION_WORKER_INTERVAL", 60)))

    def loop():
        import logging

        from django.db import close_old_connections

        log = logging.getLogger("tourist.notification_worker")
        time.sleep(10)  # let the server finish booting
        while True:
            try:
                from tourist.notification_delivery import process_due_notifications

                result = process_due_notifications(limit=100)
                if result.get("processed"):
                    log.info("notification worker: %s", result)
            except Exception as exc:  # noqa: BLE001 - never kill the worker
                log.warning("notification worker error: %s", exc)
            finally:
                close_old_connections()
            time.sleep(interval)

    threading.Thread(target=loop, name="notification-worker", daemon=True).start()
