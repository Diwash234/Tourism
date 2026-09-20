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
