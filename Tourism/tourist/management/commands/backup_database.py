"""Disaster recovery: create consistent, compressed database backups.

Uses the SQLite online backup API (safe while the app is running — no
half-written pages), writes gzip-compressed archives into the backups/
directory, records a SHA-256 checksum, and prunes old archives beyond
--keep (default 7 daily generations ~= one week RPO when run from cron).

Restore is a separate command (restore_database) that validates the
archive before touching the live database.

Usage:
    python manage.py backup_database
    python manage.py backup_database --keep 14 --dir /mnt/offsite/backups
"""
import gzip
import hashlib
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Command(BaseCommand):
    help = "Create a consistent gzip-compressed SQLite backup with retention pruning."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=None, help="Backup directory (default: <project>/backups)")
        parser.add_argument("--keep", type=int, default=7, help="How many archives to keep (default 7)")

    def handle(self, *args, **options):
        if connection.vendor != "sqlite":
            raise CommandError(
                "This command backs up the SQLite dev/staging database. For Postgres "
                "use pg_dump in your deployment pipeline (see DEPLOYMENT notes)."
            )
        backup_dir = options["dir"] or os.path.join(settings.BASE_DIR.parent, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # 1) Consistent snapshot via the SQLite backup API (works even for
        #    the in-memory test database: back up the live connection).
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sqlite3", dir=backup_dir)
        os.close(tmp_fd)
        try:
            src = connection.connection
            if src is None:
                connection.ensure_connection()
                src = connection.connection
            dst = sqlite3.connect(tmp_path)
            try:
                src.backup(dst)
            finally:
                dst.close()

            # 2) Compress
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            archive_path = os.path.join(backup_dir, f"db-{stamp}.sqlite3.gz")
            with open(tmp_path, "rb") as raw, gzip.open(archive_path, "wb", compresslevel=9) as gz:
                shutil.copyfileobj(raw, gz)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        checksum = _sha256(archive_path)
        with open(archive_path + ".sha256", "w", encoding="utf-8") as f:
            f.write(f"{checksum}  {os.path.basename(archive_path)}\n")

        # 3) Retention: keep the newest N archives
        archives = sorted(
            (os.path.join(backup_dir, n) for n in os.listdir(backup_dir) if n.endswith(".sqlite3.gz")),
            key=os.path.getmtime,
            reverse=True,
        )
        pruned = 0
        for old in archives[options["keep"]:]:
            os.remove(old)
            if os.path.exists(old + ".sha256"):
                os.remove(old + ".sha256")
            pruned += 1

        self.stdout.write(
            f"Backup written: {archive_path} ({os.path.getsize(archive_path)} bytes)\n"
            f"SHA-256: {checksum}\n"
            f"Archives kept: {min(len(archives), options['keep'])}, pruned: {pruned}"
        )
