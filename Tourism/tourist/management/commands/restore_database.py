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

        # PostgreSQL backups are raw SQL dumps — they take a dedicated path.
        if path.endswith(".sql.gz"):
            return self._restore_sql_dump(data, options)

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

    # ------------------------------------------------------------------
    # PostgreSQL SQL-dump restore (backup_database writes .sql.gz on PG)
    # ------------------------------------------------------------------
    def _pg_tools(self):
        import shutil
        tools = {}
        for key, env_override in (("psql", "PG_PSQL"), ("createdb", "PG_CREATEDB"),
                                  ("dropdb", "PG_DROPDB")):
            tools[key] = os.environ.get(env_override) or shutil.which(key)
        missing = [k for k, v in tools.items() if not v]
        if missing:
            raise SystemExit(
                "REFUSED: PostgreSQL client tools not found: " + ", ".join(missing) +
                ". Install them or set PG_PSQL/PG_CREATEDB/PG_DROPDB to full paths.")
        return tools

    def _restore_sql_dump(self, data, options):
        import re
        import subprocess
        import tempfile
        from datetime import datetime, timezone

        from django.conf import settings

        db = settings.DATABASES["default"]
        tools = self._pg_tools()
        env = dict(os.environ, PGPASSWORD=str(db.get("PASSWORD") or ""))
        conn = ["-h", str(db.get("HOST") or "localhost"),
                "-p", str(db.get("PORT") or 5432),
                "-U", str(db.get("USER") or "")]

        sql_file = tempfile.NamedTemporaryFile("wb", suffix=".sql", delete=False)
        sql_file.write(data)
        sql_file.close()

        def run(cmd):
            proc = subprocess.run(cmd, capture_output=True, env=env, text=True)
            if proc.returncode != 0:
                raise SystemExit(f"REFUSED: {' '.join(cmd[:1])} failed: "
                                 f"{proc.stderr.strip()[:400]}")
            return proc.stdout.strip()

        try:
            if options["target"]:
                # Drill: load into a throwaway database on the same server.
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                seed = re.sub(r"[^a-z0-9]", "", str(options["target"]).lower())[:40]
                scratch = f"restore_drill_{seed}_{stamp}"
                run([tools["createdb"], *conn, scratch])
                try:
                    run([tools["psql"], *conn, "-d", scratch, "--no-psqlrc",
                         "-v", "ON_ERROR_STOP=1", "--single-transaction",
                         "--quiet", "-f", sql_file.name])
                    count = run([tools["psql"], *conn, "-d", scratch, "--no-psqlrc",
                                 "-tAc", "SELECT COUNT(*) FROM tourist_destination"])
                finally:
                    run([tools["dropdb"], *conn, scratch])
                self.stdout.write(self.style.SUCCESS(
                    f"Restore drill OK: {count} destinations loaded into "
                    f"scratch {scratch}"))
                return

            if not options["confirm"]:
                raise SystemExit(
                    "REFUSED: restore overwrites the CURRENT database. "
                    "Re-run with --confirm (or use --target for a scratch drill).")

            # Live restore: protect the current database first, then rebuild.
            call_command("backup_database")
            name = str(db.get("NAME") or "")
            run([tools["dropdb"], *conn, name])
            run([tools["createdb"], *conn, name])
            run([tools["psql"], *conn, "-d", name, "--no-psqlrc",
                 "-v", "ON_ERROR_STOP=1", "--single-transaction",
                 "--quiet", "-f", sql_file.name])
            count = run([tools["psql"], *conn, "-d", name, "--no-psqlrc",
                         "-tAc", "SELECT COUNT(*) FROM tourist_destination"])
            self.stdout.write(self.style.SUCCESS(
                f"Restore complete: {count} destinations. "
                "A pre-restore backup of the previous state was created."))
        finally:
            os.unlink(sql_file.name)
