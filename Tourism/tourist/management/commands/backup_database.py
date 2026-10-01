"""
Management command to backup the database.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Backup the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default="backups",
            help="Output directory for the backup file",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = settings.DATABASES["default"]["NAME"]

        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            backup_file = output_dir / f"backup_{timestamp}.sqlite3"
            self.stdout.write(f"Creating SQLite backup: {backup_file}")

            # For SQLite, we can simply copy the file
            import shutil
            shutil.copy2(db_name, backup_file)

        elif settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
            backup_file = output_dir / f"backup_{timestamp}.sql"
            self.stdout.write(f"Creating PostgreSQL backup: {backup_file}")

            # Use pg_dump for PostgreSQL
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.DATABASES["default"]["PASSWORD"]

            cmd = [
                "pg_dump",
                "-h", settings.DATABASES["default"]["HOST"],
                "-p", str(settings.DATABASES["default"]["PORT"]),
                "-U", settings.DATABASES["default"]["USER"],
                "-d", db_name,
                "-f", str(backup_file),
            ]

            try:
                subprocess.run(cmd, env=env, check=True)
            except subprocess.CalledProcessError as exc:
                self.stderr.write(f"Backup failed: {exc}")
                return
            except FileNotFoundError:
                self.stderr.write("pg_dump not found. Please install PostgreSQL client tools.")
                return
        else:
            self.stderr.write(f"Unsupported database engine: {settings.DATABASES['default']['ENGINE']}")
            return

        self.stdout.write(self.style.SUCCESS(f"Backup created successfully: {backup_file}"))
