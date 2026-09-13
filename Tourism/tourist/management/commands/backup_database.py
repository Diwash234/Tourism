"""Production-grade database backup: gzip dump + SHA-256 sidecar + rotation.

Usage:
    python manage.py backup_database [--dir backups] [--keep 7]
"""
import gzip
import hashlib
import io
import os
from datetime import datetime, timezone

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Dump the database to backups/, verify with SHA-256, rotate old archives."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=os.path.join(str(settings.BASE_DIR), "backups"))
        parser.add_argument("--keep", type=int, default=7)

    def handle(self, *args, **options):
        out_dir = options["dir"]
        os.makedirs(out_dir, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        engine = settings.DATABASES["default"]["ENGINE"]
        ext = "sqlite" if "sqlite3" in engine else "sql"
        path = os.path.join(out_dir, f"backup-{stamp}.{ext}.gz")

        buf = io.StringIO()
        if "sqlite3" in engine:
            # Portable dump that works without external tools.
            call_command("dumpdata", "--natural-foreign", "--natural-primary",
                         "-e", "contenttypes", "-e", "auth.permission",
                         "-e", "admin.logentry", "--indent", "1", stdout=buf)
            data = buf.getvalue().encode("utf-8")
        else:
            import subprocess
            db = settings.DATABASES["default"]
            env = dict(os.environ, PGPASSWORD=str(db.get("PASSWORD") or ""))
            proc = subprocess.run(
                ["pg_dump", "-h", str(db.get("HOST") or "localhost"),
                 "-p", str(db.get("PORT") or 5432), "-U", str(db.get("USER") or ""),
                 "-d", str(db.get("NAME") or ""), "--no-owner"],
                capture_output=True, env=env, check=True)
            data = proc.stdout

        with gzip.open(path, "wb") as fh:
            fh.write(data)
        digest = hashlib.sha256(data).hexdigest()
        with open(path + ".sha256", "w") as fh:
            fh.write(f"{digest}  {os.path.basename(path)}\n")

        # verify the archive we just wrote
        with gzip.open(path, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != digest:
                raise RuntimeError(f"Backup verification FAILED for {path}")

        # rotation
        archives = sorted(f for f in os.listdir(out_dir)
                          if f.endswith(".gz") and os.path.getmtime(os.path.join(out_dir, f)))
        removed = []
        while len(archives) > options["keep"]:
            old = archives.pop(0)
            for suffix in ("", ".sha256"):
                p = os.path.join(out_dir, old + suffix)
                if os.path.exists(p):
                    os.remove(p)
            removed.append(old)

        self.stdout.write(self.style.SUCCESS(
            f"Backup OK: {path} ({len(data)} bytes, sha256={digest[:16]}...) "
            f"verified; removed={removed or 'none'}"))
