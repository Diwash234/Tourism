"""Prepare a load.json fixture for Render deployment.

This command exports all application data from the current database into a
portable JSON fixture that can be loaded into PostgreSQL on Render.

Usage:
    python manage.py prepare_render_data --output load.json
    python manage.py prepare_render_data --output load.json --exclude-users
"""
from pathlib import Path

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Export application data for Render PostgreSQL deployment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="load.json",
            help="Output fixture path (default: load.json)",
        )
        parser.add_argument(
            "--exclude-users",
            action="store_true",
            help="Exclude user accounts (for public seed data)",
        )

    def handle(self, *args, **options):
        output = Path(options["output"]).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        excludes = [
            "contenttypes",
            "auth.permission",
            "admin.logentry",
            "sessions",
            "token_blacklist",
        ]

        if options["exclude_users"]:
            excludes.extend([
                "tourist_user",
                "tourist_staffcapabilityprofile",
                "tourist_passwordresettoken",
                "tourist_emailverificationtoken",
                "tourist_smsverificationtoken",
            ])

        self.stdout.write(f"Exporting database data to {output} ...")

        with output.open("w", encoding="utf-8") as stream:
            call_command(
                "dumpdata",
                *[item for exclude in excludes for item in ("--exclude", exclude)],
                "--natural-foreign",
                "--natural-primary",
                "--indent",
                "2",
                stdout=stream,
            )

        # Verify the output
        size_mb = output.stat().st_size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(f"Created portable fixture: {output} ({size_mb:.1f} MB)"))
        self.stdout.write("")
        self.stdout.write("To use this fixture on Render:")
        self.stdout.write("  1. Copy load.json to your Render service")
        self.stdout.write("  2. The entrypoint.sh will automatically load it into PostgreSQL")
        self.stdout.write("")
        self.stdout.write("To load manually:")
        self.stdout.write(f"  python manage.py loaddata {output}")
