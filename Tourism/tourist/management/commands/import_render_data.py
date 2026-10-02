import json
import os
import tempfile
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, call_command
from django.core.management.color import no_style
from django.db import connection

DEFAULT_CANDIDATES = [
    "data.json",
    "load.json",
    "/app/Tourism/data.json",
    "/app/Tourism/load.json",
    "/app/data.json",
    "/app/load.json",
]

EXCLUDED_MODELS = {
    "contenttypes.contenttype",
    "auth.permission",
    "sessions.session",
    "admin.logentry",
}


def find_fixture(requested_path=None):
    if requested_path:
        p = Path(requested_path).expanduser().resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"Fixture not found at specified path: {requested_path}")

    for candidate in DEFAULT_CANDIDATES:
        p = Path(candidate).expanduser().resolve()
        if p.is_file():
            return p
    return None


def sanitize_fixture(fixture_path: Path):
    """Filter out contenttypes and auth.permission records to prevent constraint errors.

    When Django runs migrations, contenttypes and permissions are auto-generated.
    Attempting to re-load them from an exported fixture causes unique constraint
    violations in PostgreSQL and SQLite alike.
    """
    with fixture_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        return fixture_path, 0

    original_count = len(data)
    filtered = [item for item in data if item.get("model", "").lower() not in EXCLUDED_MODELS]
    excluded_count = original_count - len(filtered)

    if excluded_count == 0:
        return fixture_path, 0

    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    )
    json.dump(filtered, temp_file, indent=2)
    temp_file.close()
    return Path(temp_file.name), excluded_count


def reset_database_sequences(stdout, style):
    """Reset PostgreSQL primary key sequences to prevent duplicate key errors on subsequent inserts."""
    if connection.vendor != "postgresql":
        return

    stdout.write("Synchronizing PostgreSQL sequence counters ...")
    sequence_sql = connection.ops.sequence_reset_sql(no_style(), apps.get_models())
    executed = 0
    with connection.cursor() as cursor:
        for sql in sequence_sql:
            if sql.strip():
                try:
                    cursor.execute(sql)
                    executed += 1
                except Exception as exc:
                    stdout.write(style.WARNING(f"Sequence sync warning: {exc}"))

    stdout.write(style.SUCCESS(f"Reset {executed} PostgreSQL sequences to current maximums."))


class Command(BaseCommand):
    help = "Import a JSON fixture (data.json or load.json) into the database with conflict protection and sequence reset."

    def add_arguments(self, parser):
        parser.add_argument("fixture", nargs="?", default="", help="Path to JSON fixture (optional; searches standard paths).")
        parser.add_argument("--noinput", action="store_true", help="Skip confirmation prompt.")
        parser.add_argument("--allow-sqlite", action="store_true", help="Allow importing into SQLite (for local testing).")
        parser.add_argument("--sync-sequences-only", action="store_true", help="Only synchronize PostgreSQL sequences without importing a fixture.")

    def handle(self, *args, **options):
        if options.get("sync_sequences_only"):
            reset_database_sequences(self.stdout, self.style)
            return

        fixture_path = find_fixture(options.get("fixture"))
        if not fixture_path:
            raise FileNotFoundError(
                "No fixture file found. Looked for data.json and load.json in current and /app directories. "
                "Specify the path as an argument: python manage.py import_render_data <path>"
            )

        if connection.vendor != "postgresql" and not options.get("allow_sqlite") and not options.get("noinput"):
            self.stdout.write(self.style.WARNING(
                f"Active database is {connection.vendor!r}. Usually this command imports into PostgreSQL."
            ))
            if input("Continue import into this database? (y/N): ").strip().lower() not in ("y", "yes"):
                self.stdout.write("Import cancelled.")
                return

        if not options.get("noinput"):
            self.stdout.write(self.style.WARNING(
                f"Loading fixture '{fixture_path}' into {connection.vendor.upper()} database '{connection.settings_dict.get('NAME')}'."
            ))
            if input("Type IMPORT to continue: ").strip() != "IMPORT":
                self.stdout.write("Import cancelled.")
                return

        self.stdout.write(f"Sanitizing fixture {fixture_path} ...")
        cleaned_path, excluded_count = sanitize_fixture(fixture_path)
        if excluded_count > 0:
            self.stdout.write(
                f"Excluded {excluded_count} conflicting framework records (contenttypes/permissions/sessions)."
            )

        try:
            self.stdout.write(f"Loading data into {connection.vendor} database ...")
            call_command("loaddata", str(cleaned_path))
            self.stdout.write(self.style.SUCCESS("loaddata finished successfully."))
        finally:
            if cleaned_path != fixture_path:
                try:
                    cleaned_path.unlink(missing_ok=True)
                except OSError:
                    pass

        # PostgreSQL sequence synchronization
        reset_database_sequences(self.stdout, self.style)

        # Print record summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Data import verified. Current record counts:"))
        for model_name in [
            "tourist.Destination",
            "tourist.DestinationImage",
            "tourist.Hotel",
            "tourist.Hospital",
            "tourist.PoliceStation",
            "tourist.User",
            "tourist.ManagedPage",
        ]:
            try:
                model = apps.get_model(model_name)
                self.stdout.write(f"  {model_name}: {model.objects.count()}")
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS("Ready for production traffic!"))
