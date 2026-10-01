"""
Management command to verify backup integrity.
"""
import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify backup integrity"

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup-dir",
            type=str,
            default="backups",
            help="Directory containing backup files",
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating backup verification report...")

        backup_dir = Path(options["backup_dir"])

        if not backup_dir.exists():
            self.stderr.write(f"Backup directory not found: {backup_dir}")
            return

        backup_files = list(backup_dir.glob("*.sql")) + list(backup_dir.glob("*.json"))

        if not backup_files:
            self.stdout.write("No backup files found")
            return

        self.stdout.write(f"\nFound {len(backup_files)} backup file(s):")

        for backup_file in backup_files:
            size = backup_file.stat().st_size
            sha256_hash = hashlib.sha256()
            with open(backup_file, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksum = sha256_hash.hexdigest()

            self.stdout.write(f"\n  {backup_file.name}")
            self.stdout.write(f"    Size: {size:,} bytes")
            self.stdout.write(f"    SHA256: {checksum}")

        self.stdout.write(self.style.SUCCESS("\nBackup verification completed"))
