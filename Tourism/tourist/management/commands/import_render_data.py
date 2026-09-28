from pathlib import Path

from django.core.management import BaseCommand, call_command
from django.db import connection


class Command(BaseCommand):
    help = "Import a one-time SQLite-to-PostgreSQL JSON fixture."

    def add_arguments(self, parser):
        parser.add_argument("fixture", help="Path to the exported JSON fixture.")
        parser.add_argument("--noinput", action="store_true", help="Skip confirmation.")

    def handle(self, *args, **options):
        fixture = Path(options["fixture"]).expanduser().resolve()
        if not fixture.is_file():
            raise FileNotFoundError(f"Fixture not found: {fixture}")
        if connection.vendor != "postgresql":
            raise RuntimeError(
                f"Refusing import: active database is {connection.vendor!r}, not PostgreSQL."
            )
        if not options["noinput"]:
            self.stdout.write(self.style.WARNING(
                "This is a one-time import into the active PostgreSQL database."
            ))
            if input("Type IMPORT to continue: ").strip() != "IMPORT":
                self.stdout.write("Import cancelled.")
                return
        self.stdout.write(f"Loading {fixture} into PostgreSQL ...")
        call_command("loaddata", str(fixture))
        self.stdout.write(self.style.SUCCESS("PostgreSQL data import completed."))
