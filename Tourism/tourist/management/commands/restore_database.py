"""Disaster recovery: restore the SQLite database from a backup archive.

Safety rails (restore is destructive):
  * requires --yes (refuses to run interactively by accident)
  * validates the archive is a readable SQLite database (PRAGMA
    integrity_check) BEFORE touching the live file
  * takes a safety backup of the current database first, so a bad restore
    is itself reversible

Usage:
    python manage.py restore_database --from backups/db-20260913-010000.sqlite3.gz --yes
"""
import gzip
import os
import shutil
import sqlite3
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Restore the SQLite database from a .sqlite3/.sqlite3.gz backup (validates first)."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", required=True, help="Backup archive path (.sqlite3 or .sqlite3.gz)")
        parser.add_argument("--yes", action="store_true", help="Confirm the destructive restore")

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError("Restore is destructive. Re-run with --yes to confirm.")
        if connection.vendor != "sqlite":
            raise CommandError("Restore supports the SQLite dev/staging database only.")

        source = options["source"]
        if not os.path.exists(source):
            raise CommandError(f"Backup file not found: {source}")

        db_path = str(settings.DATABASES["default"]["NAME"])
        if db_path in (":memory:", "") or not os.path.sep in db_path:
            raise CommandError("Cannot restore onto an in-memory database.")

        # 1) Decompress (if needed) to a temp file and validate integrity
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(tmp_fd)
        try:
            if source.endswith(".gz"):
                with gzip.open(source, "rb") as gz, open(tmp_path, "wb") as out:
                    shutil.copyfileobj(gz, out)
            else:
                shutil.copyfile(source, tmp_path)

            con = sqlite3.connect(tmp_path)
            try:
                try:
                    result = con.execute("PRAGMA integrity_check").fetchone()
                    tables = con.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    ).fetchone()[0]
                except sqlite3.DatabaseError as exc:
                    raise CommandError(f"Archive is not a readable SQLite database: {exc}")
            finally:
                con.close()
            if not result or result[0] != "ok":
                raise CommandError(f"Archive failed integrity check: {result}")
            if tables == 0:
                raise CommandError("Archive contains no tables — refusing to restore an empty database.")

            # 2) Safety-backup the current live database (best effort)
            safety = db_path + ".pre-restore"
            if os.path.exists(db_path):
                shutil.copyfile(db_path, safety)

            # 3) Swap in the validated archive
            shutil.copyfile(tmp_path, db_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        self.stdout.write(
            f"Database restored from {source}.\n"
            f"Previous database preserved at: {safety}\n"
            "Restart the Django service so open connections pick up the restored file."
        )
