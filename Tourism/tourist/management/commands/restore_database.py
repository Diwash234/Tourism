"""Restore from a backup archive with integrity checks and explicit safeguards.

  * SHA-256 sidecar must match (corrupt backups are rejected);
  * the CURRENT database is backed up first (pre-restore safety net);
  * destructive restore requires --confirm;
  * --target lets you rehearse against a scratch database without touching
    the live one (used by the restore drill).

Usage:
    python manage.py restore_database --file backups/backup-....sqlite.gz
    python manage.py restore_database --file ... --confirm
"""
import gzip
import hashlib
import io
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify and restore a database backup; protects the current DB first."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True)
        parser.add_argument("--confirm", action="store_true",
                            help="Required to actually overwrite the current database.")
        parser.add_argument("--target", default="",
                            help="Optional scratch sqlite path to restore INTO (drill mode).")

    def handle(self, *args, **options):
        path = options["file"]
        if not os.path.exists(path):
            raise SystemExit(f"Backup file not found: {path}")

        # integrity check against the sidecar
        sidecar = path + ".sha256"
        with gzip.open(path, "rb") as fh:
            data = fh.read()
        digest = hashlib.sha256(data).hexdigest()
        if os.path.exists(sidecar):
            expected = open(sidecar).read().split()[0]
            if expected != digest:
                raise SystemExit(
                    f"REFUSED: checksum mismatch for {path} "
                    f"(expected {expected[:16]}..., got {digest[:16]}...). "
                    "The backup is corrupt; nothing was restored.")
        else:
            self.stdout.write(self.style.WARNING(
                "No .sha256 sidecar found; verifying gzip integrity only."))

        # loaddata wants a real file path: write the payload to a temp fixture
        import tempfile
        fixture = tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False)
        fixture.write(data)
        fixture.close()

        if options["target"]:
            # Drill mode: load into a scratch database, never the live one.
            target = options["target"]
            if os.path.exists(target):
                os.remove(target)
            scratch = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": target}}
            from django.test import override_settings
            with override_settings(DATABASES=scratch):
                from django.db import connections
                call_command("migrate", run_syncdb=True, verbosity=0)
                call_command("loaddata", fixture.name, verbosity=0)
                with connections["default"].cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM tourist_destination")
                    count = cur.fetchone()[0]
                connections["default"].close()
            os.unlink(fixture.name)
            self.stdout.write(self.style.SUCCESS(
                f"Restore drill OK: {count} destinations loaded into scratch {target}"))
            return

        if not options["confirm"]:
            raise SystemExit(
                "REFUSED: restore overwrites the CURRENT database. "
                "Re-run with --confirm (or use --target for a scratch drill).")

        # protect the current database first
        call_command("backup_database")
        call_command("flush", "--noinput", verbosity=0)
        call_command("loaddata", fixture.name, verbosity=0)
        os.unlink(fixture.name)
        from tourist.models import Destination
        self.stdout.write(self.style.SUCCESS(
            f"Restore complete: {Destination.objects.count()} destinations. "
            "A pre-restore backup of the previous state was created."))
