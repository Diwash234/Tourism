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
