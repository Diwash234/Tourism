"""
Import missing user accounts from the bundled legacy SQLite snapshot.

This is intentionally limited to the custom User table. It does not replace
PostgreSQL data, delete accounts, or import sessions/tokens. Existing accounts
with the same email are left untouched so a traveller can keep a password they
already changed on the new system.
"""
import gzip
import sqlite3
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Safely migrate missing user accounts from the legacy SQLite snapshot."

    DEFAULT_SNAPSHOT = "downloads/nepal-tourism-database.sqlite3.gz"

    def add_arguments(self, parser):
        parser.add_argument("--input", default=self.DEFAULT_SNAPSHOT)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        root = Path(__file__).resolve().parents[4]
        snapshot = root / options["input"]
        if not snapshot.is_file():
            self.stdout.write(self.style.WARNING(f"SQLite snapshot not found: {snapshot}"))
            return

        # Materialise the gzip to a temporary file because sqlite3 needs a
        # seekable database file.
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as tmp:
            with gzip.open(snapshot, "rb") as src:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    tmp.write(chunk)
            tmp.flush()

            conn = sqlite3.connect(tmp.name)
            conn.row_factory = sqlite3.Row
            try:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                table = "tourist_user" if "tourist_user" in tables else (
                    "auth_user" if "auth_user" in tables else None
                )
                if not table:
                    self.stdout.write(self.style.WARNING("No legacy user table found in SQLite snapshot."))
                    return

                columns = {
                    row[1]
                    for row in conn.execute(f'PRAGMA table_info("{table}")')
                }
                required = {"email", "password"}
                if not required.issubset(columns):
                    self.stdout.write(self.style.ERROR(
                        f"Legacy {table} table lacks required columns: {required - columns}"
                    ))
                    return

                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            finally:
                conn.close()

        User = get_user_model()
        created = 0
        existing = 0
        skipped = 0

        for row in rows:
            email = str(row["email"] or "").strip().lower()
            password = str(row["password"] or "")
            if not email or not password:
                skipped += 1
                continue

            if User.objects.filter(email__iexact=email).exists():
                existing += 1
                continue

            if options["dry_run"]:
                created += 1
                continue

            kwargs = {
                "email": email,
                "password": password,  # already a Django password hash
                "first_name": row["first_name"] if "first_name" in columns else "",
                "last_name": row["last_name"] if "last_name" in columns else "",
                "is_active": bool(row["is_active"]) if "is_active" in columns else True,
                "is_staff": bool(row["is_staff"]) if "is_staff" in columns else False,
                "is_superuser": bool(row["is_superuser"]) if "is_superuser" in columns else False,
                "date_joined": row["date_joined"] if "date_joined" in columns and row["date_joined"] else None,
            }
            # Only pass fields that the current custom User actually has.
            valid_fields = {f.name for f in User._meta.fields}
            kwargs = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
            User.objects.create(**kwargs)
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Legacy user migration: created={created}, existing={existing}, skipped={skipped}"
        ))
