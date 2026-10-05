"""Parallel multi-source image acquisition.

Runs multiple image sources simultaneously to fill destinations without images:
- Openverse (Creative Commons)
- Wikimedia Commons (free photos)
- Mapillary (street-level)
- Panoramax (open street-level)

Each source runs in its own thread. Results are merged.

Run:
    python manage.py acquire_parallel --limit 500
"""
import os
import sys
import threading
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
    help = "Parallel multi-source image acquisition."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        from django.db.models import Count

        # Get destinations without images
        qs = Destination.objects.filter(is_active=True).annotate(
            img_count=Count("gallery")
        ).filter(img_count=0)[: options["limit"]]

        destinations = list(qs)
        self.stdout.write(f"Processing {len(destinations)} destinations with 4 parallel sources...")

        # Shared results
        results = {"openverse": 0, "wikimedia": 0, "mapillary": 0, "panoramax": 0}
        lock = threading.Lock()

        def process_batch(batch, source_name):
            added = 0
            for dest in batch:
                try:
                    if dest.gallery.count() > 0:
                        continue

                    image_url = None

                    if source_name == "openverse":
                        image_url = self._search_openverse(dest)
                    elif source_name == "wikimedia":
                        image_url = self._search_wikimedia(dest)
                    elif source_name == "mapillary":
                        image_url = self._search_mapillary(dest)
                    elif source_name == "panoramax":
                        image_url = self._search_panoramax(dest)

                    if image_url:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=image_url,
                            source=DestinationImage.Source.WIKIMEDIA,
                            source_platform=source_name,
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            is_cover=True,
                        )
                        added += 1
                except Exception:
                    pass

            with lock:
                results[source_name] = added

        # Split destinations into 4 batches
        batch_size = max(1, len(destinations) // 4)
        batches = [
            destinations[i : i + batch_size]
            for i in range(0, len(destinations), batch_size)
        ]

        # Run 4 sources in parallel
        sources = ["openverse", "wikimedia", "mapillary", "panoramax"]
        threads = []
        for i, source in enumerate(sources):
            batch = batches[i] if i < len(batches) else []
            t = threading.Thread(target=process_batch, args=(batch, source))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        total = sum(results.values())
        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Added {total} real images: {results}"
        ))

    def _search_openverse(self, dest):
        try:
            response = requests.get(
                "https://api.openverse.org/v1/images/",
                params={"q": f"{dest.name} Nepal", "page_size": 3},
                headers={"User-Agent": "NepalTourismImageRepair/1.0"},
                timeout=10,
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                for item in results:
                    url = item.get("url")
                    if url:
                        return url
        except Exception:
            pass
        return None

    def _search_wikimedia(self, dest):
        try:
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
                timeout=10,
            )
            if response.status_code == 200:
                pages = response.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    info = (page.get("imageinfo") or [{}])[0]
                    url = info.get("thumburl") or info.get("url")
                    if url:
                        return url
        except Exception:
            pass
        return None

    def _search_mapillary(self, dest):
        if not dest.latitude or not dest.longitude:
            return None
        try:
            response = requests.get(
                "https://graph.mapillary.com/images",
                params={
                    "bbox": f"{float(dest.longitude)-0.01},{float(dest.latitude)-0.01},{float(dest.longitude)+0.01},{float(dest.latitude)+0.01}",
                    "limit": 1,
                    "fields": "id,thumb_1024_url",
                },
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    return data[0].get("thumb_1024_url")
        except Exception:
            pass
        return None

    def _search_panoramax(self, dest):
        if not dest.latitude or not dest.longitude:
            return None
        try:
            response = requests.get(
                "https://api.panoramax.xyz/api/search",
                params={
                    "lat": float(dest.latitude),
                    "lon": float(dest.longitude),
                    "distance": 1000,
                    "limit": 1,
                },
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json().get("features", [])
                if data:
                    props = data[0].get("properties", {})
                    return props.get("url")
        except Exception:
            pass
        return None
