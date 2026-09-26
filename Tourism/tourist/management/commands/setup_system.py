"""
One-command bootstrap of the entire Nepal tourism database.

This is a local/bootstrap importer for the raw CSV feeds. It does not
publish a database. For the privacy-safe shareable catalog, use
``build_verified_snapshot`` after reviewing the source data.

    python manage.py setup_system

It runs all the import/enrichment/generation steps in order. Each step is
idempotent, so it's safe to re-run.

Steps:
  1. migrate
  2. import OSM destinations (names, coordinates, categories)
  3. import hotels from hotel.csv
  4. enrich with descriptions
  5. fill only missing recorded locations (never read legacy JSON projections)
  6. optionally seed local-only E2E users/packages with --with-demo
  7. assign cover + gallery images (multi-source)
  8. backfill search embeddings

This command is for local/bootstrap experiments. It is not the public release
path; use ``build_verified_snapshot`` for a shareable database.

For actual AI image FILES (rather than external URLs), run separately:
    python manage.py download_ai_images --all --num 10
"""
import subprocess
import sys
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap the complete Nepal tourism database (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--skip-images", action="store_true",
                            help="Skip the image assignment step")
        parser.add_argument("--with-demo", action="store_true",
                            help="Explicitly add local E2E users/packages; never use for a public build")
        parser.add_argument("--noinput", action="store_true")

    def handle(self, *args, **options):
        steps = [
            ("Applying database migrations", ["migrate", "--noinput"]),
            ("Importing OSM destinations & hotels",
             ["import_osm_destinations"]),
            ("Importing hotels from hotel.csv", ["import_hotels_csv"]),
            ("Importing hospital directory", ["import_hospital"]),
            ("Importing police directory", ["import_police"]),
            ("Applying recorded city/coords from the current destination records",
             ["fill_missing_place_coords", "--no-apply", "--no-export"]),
            ("Assigning cover & gallery images",
             ["assign_destination_photos", "--stale-only"]),
            ("Backfilling search embeddings",
             ["backfill_embeddings", "--destinations"]),
        ]

        if options.get("with_demo"):
            steps.insert(5, ("Seeding local-only demo logins and marketplace packages", ["seed_e2e_features"]))
        else:
            self.stdout.write(self.style.NOTICE(
                "Skipping demo users/packages; pass --with-demo only for local E2E work."
            ))

        if options["skip_images"]:
            steps = [s for s in steps if "image" not in s[0].lower()]

        for i, (label, cmd) in enumerate(steps, 1):
            self.stdout.write(self.style.NOTICE(f"\n[{i}/{len(steps)}] {label}..."))
            try:
                call_command(*cmd)
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  step failed: {exc}")
                if "migrate" in cmd:
                    raise

        self.stdout.write(self.style.SUCCESS(
            "\nSetup complete. To download real AI image FILES run:\n"
            "  python manage.py download_ai_images --all --num 10\n"
        ))
