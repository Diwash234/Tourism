"""Fix specific missing destination images and replace postcard URLs.

1. Add real images to Pumdikot and Gupteshwar Cave (missing from itinerary)
2. Replace postcard placeholder URLs with real Wikimedia/Unsplash images
3. Never removes existing external URLs

Run:
    python manage.py fix_missing_destination_images
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
from django.conf import settings
from django.core.management.base import BaseCommand

from tourist.models import Destination, DestinationImage


class Command(BaseCommand):
    help = "Fix missing destination images and replace postcard URLs."

    def handle(self, *args, **options):
        self._fix_pumdikot()
        self._fix_gupteshwar()
        self._replace_postcards()
        self._report_status()

    def _fix_pumdikot(self):
        """Add real images to Pumdikot."""
        dest = Destination.objects.filter(name__icontains="pumdikot").first()
        if not dest:
            self.stderr.write("Pumdikot not found")
            return

        if dest.gallery.count() > 0:
            self.stdout.write(f"Pumdikot already has {dest.gallery.count()} images")
            return

        # Search Wikimedia Commons for Pumdikot
        try:
            response = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": "Pumdikot Nepal",
                    "gsrlimit": 5,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata",
                },
                headers={"User-Agent": "NepalTourismImageRepair/1.0"},
                timeout=15,
            )
            if response.status_code == 200:
                pages = response.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    info = (page.get("imageinfo") or [{}])[0]
                    url = info.get("thumburl") or info.get("url")
                    if url:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=url,
                            source=DestinationImage.Source.WIKIMEDIA,
                            source_url=info.get("descriptionurl", ""),
                            source_platform="Wikimedia Commons",
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            is_cover=True,
                        )
                        self.stdout.write(f"Added Wikimedia image to Pumdikot: {url[:60]}")
                        return
        except Exception as exc:
            self.stderr.write(f"Error fixing Pumdikot: {exc}")

        # Fallback: use Unsplash
        self._add_unsplash_image(dest, "Pumdikot Shiva statue Nepal")

    def _fix_gupteshwar(self):
        """Add real images to Gupteshwar Cave."""
        dest = Destination.objects.filter(name__icontains="gupteshwar cave").first()
        if not dest:
            self.stderr.write("Gupteshwar Cave not found")
            return

        if dest.gallery.count() > 0:
            self.stdout.write(f"Gupteshwar Cave already has {dest.gallery.count()} images")
            return

        # Search Wikimedia Commons for Gupteshwar
        try:
            response = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": "Gupteshwor Mahadev Cave Nepal",
                    "gsrlimit": 5,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata",
                },
                headers={"User-Agent": "NepalTourismImageRepair/1.0"},
                timeout=15,
            )
            if response.status_code == 200:
                pages = response.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    info = (page.get("imageinfo") or [{}])[0]
                    url = info.get("thumburl") or info.get("url")
                    if url:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=url,
                            source=DestinationImage.Source.WIKIMEDIA,
                            source_url=info.get("descriptionurl", ""),
                            source_platform="Wikimedia Commons",
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            is_cover=True,
                        )
                        self.stdout.write(f"Added Wikimedia image to Gupteshwar: {url[:60]}")
                        return
        except Exception as exc:
            self.stderr.write(f"Error fixing Gupteshwar: {exc}")

        # Fallback: use Unsplash
        self._add_unsplash_image(dest, "Gupteshwar Mahadev Cave Pokhara Nepal")

    def _add_unsplash_image(self, dest, query):
        """Add an Unsplash image to a destination."""
        access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "")
        if not access_key:
            return

        try:
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 3, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {access_key}"},
                timeout=15,
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    photo = results[0]
                    img_url = photo.get("urls", {}).get("regular") or photo.get("urls", {}).get("small")
                    if img_url:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=img_url,
                            source=DestinationImage.Source.UNSPLASH,
                            source_url=photo.get("links", {}).get("html", ""),
                            source_platform="Unsplash",
                            photographer=photo.get("user", {}).get("name", ""),
                            license_type="Unsplash License",
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            is_cover=True,
                        )
                        self.stdout.write(f"Added Unsplash image to {dest.name}")
        except Exception as exc:
            self.stderr.write(f"Error adding Unsplash image: {exc}")

    def _replace_postcards(self):
        """Replace postcard placeholder URLs with real images."""
        postcard_imgs = DestinationImage.objects.filter(external_url__icontains="postcard")
        count = postcard_imgs.count()
        self.stdout.write(f"Found {count} postcard images to replace")

        for img in postcard_imgs:
            dest = img.destination
            # Try to find a real image for this destination
            real_img = DestinationImage.objects.filter(
                destination=dest
            ).exclude(
                external_url__icontains="postcard"
            ).exclude(
                external_url=""
            ).first()

            if real_img:
                # Replace postcard with real image
                img.external_url = real_img.external_url
                img.source = real_img.source
                img.source_url = real_img.source_url
                img.source_platform = real_img.source_platform
                img.photographer = real_img.photographer
                img.license_type = real_img.license_type
                img.save()
            else:
                # Try Unsplash
                self._add_unsplash_image(dest, f"{dest.name} Nepal")

        self.stdout.write(self.style.SUCCESS("Done replacing postcards"))

    def _report_status(self):
        total = Destination.objects.filter(is_active=True).count()
        from django.db.models import Count
        with_img = Destination.objects.filter(is_active=True).annotate(ic=Count("gallery")).filter(ic__gt=0).count()
        print(f"\nDestinations with images: {with_img}/{total} ({100*with_img//total}%)")

        postcards = DestinationImage.objects.filter(external_url__icontains="postcard").count()
        print(f"Postcard images remaining: {postcards}")
