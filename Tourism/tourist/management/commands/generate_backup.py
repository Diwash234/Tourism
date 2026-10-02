"""
Management command to create a database backup.
"""
import gzip
import os
import shutil
from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a compressed database backup"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default="backups",
            help="Output directory for the backup file",
        )
        parser.add_argument(
            "--compress",
            action="store_true",
            default=True,
            help="Compress the backup with gzip",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = output_dir / f"backup_{timestamp}.json"

        self.stdout.write(f"Creating backup: {backup_file}")

        # Use Django's dumpdata to create the backup
        with open(backup_file, "w", encoding="utf-8") as f:
            call_command("dumpdata", "--exclude", "contenttypes", "--exclude", "auth.permission", stdout=f)

        # Compress if requested
        if options["compress"]:
            compressed_file = Path(f"{backup_file}.gz")
            self.stdout.write(f"Compressing to: {compressed_file}")
            with open(backup_file, "rb") as f_in:
                with gzip.open(compressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file.unlink()  # Remove uncompressed file
            backup_file = compressed_file

        size = backup_file.stat().st_size
        self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_file} ({size:,} bytes)"))
