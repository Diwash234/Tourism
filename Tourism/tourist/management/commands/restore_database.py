"""
Management command to restore the database from a backup.
"""
import os
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Restore the database from a backup"

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup-file",
            type=str,
            required=True,
            help="Path to the backup file",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        backup_file = Path(options["backup_file"])
        force = options["force"]

        if not backup_file.exists():
            self.stderr.write(f"Backup file not found: {backup_file}")
            return

        if not force:
            confirm = input(f"This will replace the current database with {backup_file}. Continue? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write("Restore cancelled.")
                return

        db_name = settings.DATABASES["default"]["NAME"]

        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            self.stdout.write(f"Restoring SQLite database from: {backup_file}")

            # For SQLite, we can simply copy the file back
            import shutil
            shutil.copy2(backup_file, db_name)

        elif settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
            self.stdout.write(f"Restoring PostgreSQL database from: {backup_file}")

            # Use psql for PostgreSQL
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.DATABASES["default"]["PASSWORD"]

            cmd = [
                "psql",
                "-h", settings.DATABASES["default"]["HOST"],
                "-p", str(settings.DATABASES["default"]["PORT"]),
                "-U", settings.DATABASES["default"]["USER"],
                "-d", db_name,
                "-f", str(backup_file),
            ]

            try:
                subprocess.run(cmd, env=env, check=True)
            except subprocess.CalledProcessError as exc:
                self.stderr.write(f"Restore failed: {exc}")
                return
            except FileNotFoundError:
                self.stderr.write("psql not found. Please install PostgreSQL client tools.")
                return
        else:
            self.stderr.write(f"Unsupported database engine: {settings.DATABASES['default']['ENGINE']}")
            return

        self.stdout.write(self.style.SUCCESS("Database restored successfully"))
