"""Acquire real destination photos from Unsplash API.

Uses the Unsplash API to search for place-specific photos and stores
them as DestinationImage records. Only processes destinations without
images. Never removes existing images.

Run:
    python manage.py acquire_unsplash_images --limit 100
    python manage.py acquire_unsplash_images --all --workers 4
"""
import os
import sys
import time
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from tourist.models import Destination, DestinationImage


class Command(BaseCommand):
    help = "Acquire real destination photos from Unsplash API."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--workers", type=int, default=1)

    def handle(self, *args, **options):
        access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "")
        if not access_key:
            self.stderr.write("UNSPLASH_ACCESS_KEY not configured")
            return

        # Get destinations without images
        from django.db.models import Count
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
                # Search Unsplash for this destination
                response = requests.get(
                    "https://api.unsplash.com/search/photos",
                    params={
                        "query": f"{dest.name} Nepal",
                        "per_page": 5,
                        "orientation": "landscape",
                    },
                    headers={"Authorization": f"Client-ID {access_key}"},
                    timeout=15,
                )
                if response.status_code != 200:
                    self.stderr.write(f"  Unsplash error for {dest.name}: {response.status_code}")
                    continue

                results = response.json().get("results", [])
                if not results:
                    continue

                # Add the first result as a destination image
                photo = results[0]
                img_url = photo.get("urls", {}).get("regular") or photo.get("urls", {}).get("small")
                if not img_url:
                    continue

                # Check if this URL already exists
                if DestinationImage.objects.filter(destination=dest, external_url=img_url).exists():
                    continue

                DestinationImage.objects.create(
                    destination=dest,
                    external_url=img_url,
                    source=DestinationImage.Source.UNSPLASH,
                    source_url=photo.get("links", {}).get("html", ""),
                    source_platform="Unsplash",
                    photographer=photo.get("user", {}).get("name", ""),
                    license_type="Unsplash License",
                    attribution=f"Photo by {photo.get('user', {}).get('name', '')} on Unsplash",
                    verification_status=DestinationImage.ImageStatus.APPROVED,
                    is_verified=True,
                    is_cover=True,
                )
                added += 1

                if i % 10 == 0:
                    self.stdout.write(f"  ... {i}/{len(destinations)} ({added} added)")

                # Rate limit: 50 requests/hour for free tier
                time.sleep(1)

            except Exception as exc:
                self.stderr.write(f"  Error for {dest.name}: {exc}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. Added {added} real Unsplash images."))
