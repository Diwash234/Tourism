"""Bootstrap a fresh PostgreSQL database from the versioned public SQLite seed.

This is intentionally only used when the target PostgreSQL catalogue is empty.
The seed is opened as SQLite, exported through Django's serializer, then loaded
into the active PostgreSQL connection. No SQLite database file is copied into
PostgreSQL.
"""
from __future__ import annotations

import gzip
import shutil
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core import serializers
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection


ARCHIVE = Path(settings.BASE_DIR).parent / "downloads" / "nepal-tourism-seed.sqlite3.gz"
SOURCE_MODELS = [
    "tourist.language",
    "tourist.category",
    "tourist.destination",
    "tourist.destinationimage",
    "tourist.hotel",
    "tourist.hospital",
    "tourist.policestation",
    "tourist.restaurant",
    "tourist.osmessentialservice",
    "tourist.destinationtransitroute",
]


class Command(BaseCommand):
    help = "Import the public SQLite seed into an empty PostgreSQL catalogue."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("This command is only for PostgreSQL targets.")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tourist_destination")
            if cursor.fetchone()[0]:
                self.stdout.write("PostgreSQL catalogue is not empty; nothing imported.")
                return
        if not ARCHIVE.is_file():
            raise CommandError(f"Seed archive not found: {ARCHIVE}")

        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        tmp.close()
        sqlite_path = Path(tmp.name)
        try:
            with gzip.open(ARCHIVE, "rb") as src, sqlite_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            probe = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
            try:
                count = probe.execute("SELECT COUNT(*) FROM tourist_destination").fetchone()[0]
                if count < 1000:
                    raise CommandError(f"Seed catalogue looks truncated: {count} destinations.")
            finally:
                probe.close()

            previous = connection.settings_dict.get("NAME")
            connection.close()
            settings.DATABASES["default"]["NAME"] = str(sqlite_path)
            connection.settings_dict["NAME"] = str(sqlite_path)
            try:
                payload = serializers.serialize("json", self._querysets(), indent=0)
            finally:
                connection.close()
                settings.DATABASES["default"]["NAME"] = previous
                connection.settings_dict["NAME"] = previous

            call_command("loaddata", StringIO(payload), format="json", verbosity=0)
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM tourist_destination")
                imported = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM tourist_destinationimage")
                images = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(
                f"PostgreSQL seed import complete: destinations={imported}, images={images}"
            ))
        finally:
            sqlite_path.unlink(missing_ok=True)

    def _querysets(self):
        from django.apps import apps
        return [
            apps.get_model(app_label, model_name)._default_manager.all()
            for app_label, model_name in (
                item.split(".", 1) for item in SOURCE_MODELS
            )
        ]
