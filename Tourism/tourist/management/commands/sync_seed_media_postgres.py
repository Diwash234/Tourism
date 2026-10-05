"""Backfill missing destination media from the verified public seed.

Only destinations with no usable gallery image are changed. Matching is by
stable slug first, then exact normalized name. Existing media and admin
corrections are never overwritten.

Reading the seed archive
------------------------
The archive is a gzipped SQLite database, but this command only ever runs
against PostgreSQL. It used to open it by pointing the *default* connection at
the extracted file::

    connection.settings_dict["NAME"] = str(sqlite_path)

That only rewrites NAME, leaving ENGINE/HOST/PORT as PostgreSQL, so psycopg
asked the server for a database literally named ``/tmp/tmpXXXXXXXX.sqlite3`` and
the boot died with::

    FATAL:  database "/tmp/tmpXXXXXXXX.sqlite3" does not exist

It could never have succeeded: the guard above skips non-PostgreSQL, and on
PostgreSQL the connection it built was invalid. Every Render deploy logged
``media backfill skipped``. The archive is now read through a dedicated SQLite
connection alias so the default PostgreSQL connection is never touched.

Cost
----
The per-destination "does it already have media?" check was two queries for
every destination -- roughly 26,000 queries over an 8,800-row catalogue, on
every single boot. The set of destinations that already have media is now
computed once with two aggregate queries and excluded in a single filter.
"""
from __future__ import annotations

import gzip
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import connections, connection

from tourist.models import Destination, DestinationImage


ARCHIVE = Path(settings.BASE_DIR).parent / "downloads" / "nepal-tourism-seed.sqlite3.gz"

# Connection alias used to read the extracted SQLite archive. Registered and
# removed per run; the default alias is never modified.
SEED_ALIAS = "seed_archive"

# Cap per destination so one bad name match cannot import an unbounded gallery.
MAX_IMAGES_PER_DESTINATION = 6


class Command(BaseCommand):
    help = "Backfill missing destination media from the verified public seed."

    def _register_seed_connection(self, sqlite_path: Path) -> None:
        """Add a standalone SQLite connection for reading the archive."""
        connections.databases[SEED_ALIAS] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(sqlite_path),
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
            "OPTIONS": {},
            "TIME_ZONE": None,
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
            "TEST": {"CHARSET": None, "COLLATION": None, "MIGRATE": False, "MIRROR": None},
        }

    def _unregister_seed_connection(self) -> None:
        try:
            connections[SEED_ALIAS].close()
        except Exception:  # pragma: no cover - best effort cleanup
            pass
        connections.databases.pop(SEED_ALIAS, None)

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write("Media seed sync is intended for PostgreSQL; skipping.")
            return
        if not ARCHIVE.is_file():
            raise CommandError(f"Seed archive not found: {ARCHIVE}")

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            sqlite_path = Path(tmp.name)
        try:
            with gzip.open(ARCHIVE, "rb") as src, sqlite_path.open("wb") as dst:
                dst.write(src.read())

            # Read the archive over its own SQLite connection. The default
            # PostgreSQL connection stays exactly as configured.
            self._register_seed_connection(sqlite_path)
            try:
                source_rows = list(
                    DestinationImage.objects.using(SEED_ALIAS)
                    .filter(
                        destination__isnull=False,
                        external_url__gt="",
                    )
                    .values(
                        "destination__slug", "destination__name", "external_url",
                        "caption", "is_cover", "verification_status", "source",
                        "source_url", "source_platform", "photographer",
                        "license_type", "copyright_status", "alt_text",
                    )
                )
            finally:
                self._unregister_seed_connection()

            if not source_rows:
                self.stdout.write("Seed archive contained no external images; nothing to do.")
                return

            by_slug = {}
            by_name = {}
            for row in source_rows:
                by_slug.setdefault(row["destination__slug"], []).append(row)
                key = " ".join((row["destination__name"] or "").casefold().split())
                by_name.setdefault(key, []).append(row)

            # Which destinations already have usable media? Two set-valued
            # queries instead of two `exists()` calls per destination.
            with_external = set(
                DestinationImage.objects.filter(external_url__gt="")
                .values_list("destination_id", flat=True)
                .distinct()
            )
            with_upload = set(
                DestinationImage.objects.filter(image__isnull=False)
                .exclude(image="")
                .values_list("destination_id", flat=True)
                .distinct()
            )
            already_covered = with_external | with_upload

            missing = Destination.objects.exclude(pk__in=already_covered)
            total_missing = missing.count()
            self.stdout.write(
                f"{total_missing} destination(s) have no usable media; matching against "
                f"{len(source_rows)} seed image(s)."
            )

            created = 0
            covers = 0
            for destination in missing.iterator(chunk_size=500):
                rows = by_slug.get(destination.slug) or by_name.get(
                    " ".join((destination.name or "").casefold().split()), []
                )
                if not rows:
                    continue
                for row in rows[:MAX_IMAGES_PER_DESTINATION]:
                    DestinationImage.objects.create(
                        destination=destination,
                        external_url=row["external_url"],
                        caption=row["caption"] or destination.name,
                        is_cover=bool(row["is_cover"]),
                        verification_status=row["verification_status"]
                        or DestinationImage.ImageStatus.APPROVED,
                        source=row["source"] or DestinationImage.Source.ADMIN,
                        source_url=row["source_url"] or "",
                        source_platform=row["source_platform"] or "",
                        photographer=row["photographer"] or "",
                        license_type=row["license_type"] or "",
                        copyright_status=row["copyright_status"] or "",
                        alt_text=row["alt_text"] or destination.name,
                    )
                    created += 1
                    if row["is_cover"]:
                        covers += 1

            self.stdout.write(self.style.SUCCESS(
                f"Destination media seed sync: created={created}, covers={covers}"
            ))
        finally:
            sqlite_path.unlink(missing_ok=True)
