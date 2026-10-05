"""Add cover images to hospitals missing them.

Uses an existing destination image from the DB as a template.
Never overwrites existing images.

Run:
    python manage.py add_hospital_images
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

from tourist.models import Destination, Hospital


class Command(BaseCommand):
    help = "Add cover images to hospitals missing them."

    def handle(self, *args, **options):
        # Find a template image — try destination gallery first, then branding
        template = None
        for d in Destination.objects.filter(is_active=True).exclude(gallery=None).distinct()[:50]:
            img = d.gallery.first()
            if img and img.image:
                try:
                    with open(img.image.path, "rb") as f:
                        template = f.read()
                        break
                except (OSError, ValueError):
                    continue

        if not template:
            # Fall back to branding logo
            logo_path = ROOT / "Tourism" / "media" / "branding" / "logo.png"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    template = f.read()

        if not template:
            self.stderr.write("No template image found")
            return

        hospitals_without = Hospital.objects.filter(image="") | Hospital.objects.filter(image=None)
        count = hospitals_without.count()
        self.stdout.write(f"Adding images to {count} hospitals...")

        added = 0
        for i, h in enumerate(hospitals_without.iterator(), 1):
            try:
                h.image.save(f"hospital_{h.id}.jpg", ContentFile(template), save=True)
                added += 1
            except Exception as exc:
                self.stderr.write(f"  Failed for {h.name}: {exc}")
            if i % 50 == 0:
                self.stdout.write(f"  ... {i}/{count}")

        self.stdout.write(self.style.SUCCESS(f"Done. Added images to {added} hospitals."))
