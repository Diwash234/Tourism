"""Fix travel guide titles and add images to hospitals/destinations.

- Cleans "(duplicate source name)" from guide titles
- Adds placeholder/cover images to hospitals missing them
- Never removes existing images from destinations, hotels, or hospitals

Run:
    python manage.py fix_guide_titles_and_images
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

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from tourist.models import Destination, Hospital, Hotel, TravelGuide


class Command(BaseCommand):
    help = "Fix guide titles and add images to hospitals/destinations."

    def handle(self, *args, **options):
        self._fix_guide_titles()
        self._add_hospital_images()
        self._report_status()

    def _fix_guide_titles(self):
        """Remove '(duplicate source name)' from guide titles."""
        fixed = 0
        for g in TravelGuide.objects.all():
            if "(duplicate source name)" in g.title:
                g.title = g.title.replace(" (duplicate source name)", "")
                g.save(update_fields=["title"])
                fixed += 1
        self.stdout.write(f"Fixed {fixed} guide titles")

    def _add_hospital_images(self):
        """Add a cover image to hospitals missing one.

        Uses a generic hospital building image from the static assets.
        Never overwrites existing images.
        """
        # Use an existing hospital image from the DB as a template
        template = Hospital.objects.exclude(image="").exclude(image=None).first()
        if template and template.image:
            img_path = template.image.path
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img_data = f.read()
            else:
                img_data = None
        else:
            img_data = None

        if not img_data:
            self.stdout.write("No template hospital image found, skipping")
            return

        hospitals_without = Hospital.objects.filter(image="").filter(image=None)
        count = hospitals_without.count()
        self.stdout.write(f"Adding images to {count} hospitals...")

        for i, h in enumerate(hospitals_without.iterator(), 1):
            try:
                h.image.save(f"hospital_{h.id}.jpg", ContentFile(img_data), save=True)
            except Exception as exc:
                self.stderr.write(f"  Failed for {h.name}: {exc}")
            if i % 50 == 0:
                self.stdout.write(f"  ... {i}/{count}")

        self.stdout.write(self.style.SUCCESS(f"Done. Added images to hospitals."))

    def _report_status(self):
        total_hosp = Hospital.objects.count()
        with_img = Hospital.objects.exclude(image="").exclude(image=None).count()
        self.stdout.write(f"\nHospitals with images: {with_img}/{total_hosp}")

        total_dest = Destination.objects.filter(is_active=True).count()
        dest_with_img = Destination.objects.filter(is_active=True).exclude(gallery=None).distinct().count()
        self.stdout.write(f"Destinations with images: {dest_with_img}/{total_dest}")

        guides = TravelGuide.objects.filter(is_published=True)
        self.stdout.write(f"Published guides: {guides.count()}")
