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
        backup_dir = Path(options["backup_dir"])

        self.stdout.write("=" * 60)
        self.stdout.write("BACKUP VERIFICATION REPORT")
        self.stdout.write("=" * 60)

        if not backup_dir.exists():
            self.stderr.write(f"Backup directory not found: {backup_dir}")
            return

        backup_files = list(backup_dir.glob("*.sql")) + list(backup_dir.glob("*.json"))
        self.stdout.write(f"\nFound {len(backup_files)} backup file(s)")

        for backup_file in backup_files:
            self.stdout.write(f"\nVerifying: {backup_file.name}")

            # Check file size
            size = backup_file.stat().st_size
            self.stdout.write(f"  Size: {size:,} bytes")

            # Calculate checksum
            sha256_hash = hashlib.sha256()
            with open(backup_file, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksum = sha256_hash.hexdigest()
            self.stdout.write(f"  SHA256: {checksum}")

            # Check if file is readable
            try:
                with open(backup_file, "r") as f:
                    f.read(1)
                self.stdout.write("  Status: OK")
            except Exception as exc:
                self.stdout.write(f"  ERROR: {exc}")

        self.stdout.write("\n" + "=" * 60)
