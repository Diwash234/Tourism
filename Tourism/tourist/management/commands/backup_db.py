"""
Management command to backup the database.
"""
import subprocess
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Backup the database to a SQL dump file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="backups",
            help="Output directory for the backup file",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = output_dir / f"backup_{timestamp}.sql"

        self.stdout.write(f"Creating database backup: {backup_file}")

        # Use Django's dumpdata for a JSON backup (works with any database)
        from django.core.management import call_command
        with open(backup_file, "w") as f:
            call_command("dumpdata", "--exclude", "contenttypes", "--exclude", "auth.permission", stdout=f)

        self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_file}"))
