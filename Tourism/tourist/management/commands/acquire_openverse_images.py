"""Acquire real destination photos from Openverse API.

Openverse is free, no API key required, no rate limits. Searches for
Creative Commons licensed images of each destination.

Run:
    python manage.py acquire_openverse_images --limit 500
    python manage.py acquire_openverse_images --all
"""
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

import requests
from django.core.management.base import BaseCommand

from tourist.models import Destination, DestinationImage


class Command(BaseCommand):
    help = "Acquire real destination photos from Openverse API."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--all", action="store_true")

    def handle(self, *args, **options):
        from django.db.models import Count

        # Get destinations without images
        qs = Destination.objects.filter(is_active=True).annotate(
            img_count=Count("gallery")
        ).filter(img_count=0)

        if not options["all"]:
            qs = qs[:options["limit"]]

        destinations = list(qs)
        self.stdout.write(f"Processing {len(destinations)} destinations without images...")

        added = 0
        for i, dest in enumerate(destinations, 1):
            try:
                # Search Openverse for this destination
                response = requests.get(
                    "https://api.openverse.org/v1/images/",
                    params={
                        "q": f"{dest.name} Nepal",
                        "page_size": 5,
                        "license_type": "all",
                    },
                    headers={"User-Agent": "NepalTourismImageRepair/1.0"},
                    timeout=15,
                )
                if response.status_code != 200:
                    continue

                results = response.json().get("results", [])
                for item in results:
                    url = item.get("url")
                    if not url:
                        continue

                    # Check if this URL already exists
                    if DestinationImage.objects.filter(destination=dest, external_url=url).exists():
                        continue

                    creator = item.get("creator", "")
                    license_name = f"{item.get('license', '')} {item.get('license_version', '')}".strip()

                    DestinationImage.objects.create(
                        destination=dest,
                        external_url=url,
                        source=DestinationImage.Source.UNSPLASH,
                        source_url=item.get("foreign_landing_url", ""),
                        source_platform="Openverse",
                        photographer=creator[:150] if creator else "",
                        license_type=license_name[:100] if license_name else "CC BY",
                        attribution=f"{creator} / {license_name}"[:255] if creator else "",
                        verification_status=DestinationImage.ImageStatus.APPROVED,
                        is_verified=True,
                        is_cover=True,
                    )
                    added += 1
                    break

                if i % 50 == 0:
                    self.stdout.write(f"  ... {i}/{len(destinations)} ({added} added)")

            except Exception as exc:
                self.stderr.write(f"  Error for {dest.name}: {exc}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. Added {added} real Openverse images."))
