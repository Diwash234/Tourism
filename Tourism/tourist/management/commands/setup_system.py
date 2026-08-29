"""
One-command bootstrap of the entire Nepal tourism database.

This is how the large dataset (6,900+ destinations and 80,000+ images) is
distributed without committing a 380MB SQLite file to git. After cloning the
repo, run:

    python manage.py setup_system

It runs all the import/enrichment/generation steps in order. Each step is
idempotent, so it's safe to re-run.

Steps:
  1. migrate
  2. import OSM destinations (names, coordinates, categories)
  3. import hotels from hotel.csv
  4. enrich with descriptions
  5. assign cover + gallery images (multi-source)
  6. backfill search embeddings

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
        parser.add_argument("--noinput", action="store_true")

    def handle(self, *args, **options):
        steps = [
            ("Applying database migrations", ["migrate", "--noinput"]),
            ("Importing OSM destinations & hotels",
             ["import_osm_destinations"]),
            ("Importing hotels from hotel.csv", ["import_hotels_csv"]),
            ("Importing hospital directory", ["import_hospital"]),
            ("Importing police directory", ["import_police"]),
            ("Applying recorded city/coords from destination_locations.json",
             ["fill_missing_place_coords"]),
            ("Seeding demo logins and marketplace packages", ["seed_e2e_features"]),
            ("Assigning cover & gallery images",
             ["assign_destination_photos", "--stale-only"]),
            ("Backfilling search embeddings",
             ["backfill_embeddings", "--destinations"]),
        ]

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
