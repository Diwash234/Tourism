"""Audit and align Destination.cover_image with verified, place-specific gallery photos.

Removes fake/reused stock photos (e.g. Vintage Rotary Dial Phone, Lumbini photos
attached to Solukhumbu lodges, Unsplash stock assets) and aligns each destination's
cover_image field with honest verified gallery media.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from tourist.models import Destination
from tourist.serializers import is_destination_specific_image, public_destination_cover
from tourist.views_admin import _recompute_destination_cover


class Command(BaseCommand):
    help = "Align Destination.cover_image with verified place-specific media."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without modifying the database.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        total = Destination.objects.count()
        checked = 0
        cleared_fake = 0
        updated_valid = 0

        self.stdout.write(f"Auditing {total} destination records for authentic covers...")

        for destination in Destination.objects.all().iterator(chunk_size=500):
            checked += 1
            current = (destination.cover_image.name if destination.cover_image else "").strip()
            verified_cover = (public_destination_cover(destination) or "").strip()

            # Disqualify non-specific gallery images from being marked as cover
            for photo in destination.gallery.filter(is_cover=True):
                if not is_destination_specific_image(destination, photo):
                    if not dry_run:
                        photo.is_cover = False
                        photo.save(update_fields=["is_cover", "updated_at"])

            if current != verified_cover:
                if not verified_cover:
                    cleared_fake += 1
                else:
                    updated_valid += 1

                if not dry_run:
                    destination.cover_image = verified_cover
                    destination.save(update_fields=["cover_image", "updated_at"])

        status_msg = (
            f"Finished cover audit: checked={checked}, cleared_fake_covers={cleared_fake}, "
            f"updated_valid_covers={updated_valid}"
        )
        if dry_run:
            status_msg += " (DRY RUN - no database writes performed)"
        self.stdout.write(self.style.SUCCESS(status_msg))
