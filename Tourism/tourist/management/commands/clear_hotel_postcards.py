"""Clear postcard images from hotels and prepare for real image repair.

Postcard URLs (/api/v1/postcard/...) are generated placeholders, not real
photos. This command clears them so the repair command can find real
Wikimedia Commons images.

Run:
    python manage.py clear_hotel_postcards
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

from django.core.management.base import BaseCommand

from tourist.models import Hotel


class Command(BaseCommand):
    help = "Clear postcard placeholder images from hotels."

    def handle(self, *args, **options):
        # Find hotels with postcard URLs
        postcard_hotels = Hotel.objects.filter(cover_image__icontains="postcard")
        count = postcard_hotels.count()
        self.stdout.write(f"Found {count} hotels with postcard images")

        # Clear the postcard cover images
        for h in postcard_hotels:
            h.cover_image = ""
            h.external_image_url = ""
            h.save(update_fields=["cover_image", "external_image_url"])

        self.stdout.write(self.style.SUCCESS(f"Cleared postcard images from {count} hotels"))
