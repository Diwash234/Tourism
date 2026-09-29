"""
Management command to restore the database from a backup.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Restore the database from a JSON backup file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
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
        file_path = Path(options["file"])
        force = options["force"]

        if not file_path.exists():
            self.stderr.write(f"File not found: {file_path}")
            return

        if not force:
            confirm = input(f"This will replace all current data with {file_path}. Continue? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write("Restore cancelled.")
                return

        self.stdout.write(f"Restoring database from {file_path}...")

        from django.core.management import call_command
        call_command("flush", "--noinput")
        call_command("loaddata", str(file_path))

        self.stdout.write(self.style.SUCCESS("Database restored successfully."))
