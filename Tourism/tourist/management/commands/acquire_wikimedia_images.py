"""Acquire real destination photos from Wikimedia Commons API.

Wikimedia Commons has no rate limits and provides real place-specific
photos with proper attribution. Processes destinations without images.

Run:
    python manage.py acquire_wikimedia_images --limit 500
    python manage.py acquire_wikimedia_images --all
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
    help = "Acquire real destination photos from Wikimedia Commons API."

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
                # Search Wikimedia Commons for this destination
                response = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "generator": "search",
                        "gsrsearch": f"{dest.name} Nepal",
                        "gsrlimit": 3,
                        "prop": "imageinfo",
                        "iiprop": "url|extmetadata",
                    },
                    headers={"User-Agent": "NepalTourismImageRepair/1.0"},
                    timeout=15,
                )
                if response.status_code != 200:
                    continue

                pages = response.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    info = (page.get("imageinfo") or [{}])[0]
                    url = info.get("thumburl") or info.get("url")
                    if not url:
                        continue

                    # Check if this URL already exists
                    if DestinationImage.objects.filter(destination=dest, external_url=url).exists():
                        continue

                    meta = info.get("extmetadata") or {}
                    license_name = (meta.get("LicenseShortName") or {}).get("value", "")
                    author = (meta.get("Artist") or {}).get("value", "")

                    DestinationImage.objects.create(
                        destination=dest,
                        external_url=url,
                        source=DestinationImage.Source.WIKIMEDIA,
                        source_url=info.get("descriptionurl", ""),
                        source_platform="Wikimedia Commons",
                        photographer=author[:150] if author else "",
                        license_type=license_name[:100] if license_name else "CC BY-SA",
                        attribution=f"{author} / {license_name}"[:255] if author else "",
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

        self.stdout.write(self.style.SUCCESS(f"\nDone. Added {added} real Wikimedia images."))
