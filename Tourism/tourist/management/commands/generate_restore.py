"""
Management command to restore a database from a backup.
"""
import gzip
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Restore the database from a backup file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup-file",
            type=str,
            required=True,
            help="Path to the backup file (plain JSON or .gz compressed)",
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
            self.stderr.write(self.style.ERROR(f"Backup file not found: {backup_file}"))
            return

        if not force:
            confirm = input(f"This will replace all current data with {backup_file}. Continue? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write("Restore cancelled.")
                return

        # Decompress if needed
        if backup_file.suffix == ".gz":
            self.stdout.write("Decompressing backup...")
            decompressed = backup_file.with_suffix("")
            with gzip.open(backup_file, "rb") as f_in:
                with open(decompressed, "wb") as f_out:
                    f_out.write(f_in.read())
            backup_file = decompressed

        self.stdout.write(f"Restoring from: {backup_file}")
        call_command("loaddata", str(backup_file))
        self.stdout.write(self.style.SUCCESS("Database restored successfully"))
