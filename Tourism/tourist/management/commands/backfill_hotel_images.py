"""
Backfills a real, hotel-specific photo for every Hotel that doesn't have
one yet, using the same Unsplash -> Wikimedia chain as
backfill_destination_images, via fetch_unsplash_photo() /
fetch_wikimedia_photos() in tourist/utils.py.

ADDED: Hotel already has cover_image / external_image_url fields on the
model (migration 0007), but nothing has ever populated them, and
HotelSerializer.get_image_url() used to skip straight past them and
reuse the parent destination's cover photo for every hotel (fixed
separately in serializers.py). This command is the other half of that
fix: it actually fetches and saves a real photo per hotel, searching
"<hotel name> <destination name> Nepal hotel" so results are specific
to the hotel rather than the general area.

Usage:
    python manage.py backfill_hotel_images
    python manage.py backfill_hotel_images --limit 50   # test run
"""
import sys
import time

from django.core.management.base import BaseCommand

from tourist.models import Hotel
from tourist.utils import fetch_unsplash_photo, fetch_wikimedia_photos


class Command(BaseCommand):
    help = "Fetch and save a cover photo (Unsplash/Wikimedia) for every hotel missing one."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=None,
            help="Only process this many hotels (useful for a test run before UNSPLASH_ACCESS_KEY is confirmed working).",
        )
        parser.add_argument(
            "--sleep", type=float, default=0.5,
            help="Seconds to sleep between hotels, to stay well under Unsplash/Wikimedia rate limits (default 0.5s).",
        )

    def handle(self, *args, **options):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

        queryset = Hotel.objects.filter(cover_image="", external_image_url="")
        if options["limit"]:
            queryset = queryset[: options["limit"]]

        total = queryset.count() if options["limit"] is None else len(queryset)
        self.stdout.write(f"Found {total} hotel(s) with no photo at all.")

        fetched, skipped, errored = 0, 0, 0
        for i, hotel in enumerate(queryset, start=1):
            destination_name = getattr(hotel.destination, "name", "") or ""
            query = f"{hotel.name} {destination_name} Nepal hotel".strip()

            try:
                photo = fetch_unsplash_photo(query)
                if not photo:
                    wiki_results = fetch_wikimedia_photos([query], limit=1)
                    photo = wiki_results[0] if wiki_results else None
            except Exception as exc:  # noqa: BLE001 -- one bad hotel must never kill the run
                errored += 1
                self.stdout.write(self.style.ERROR(
                    f"  [{i}/{total}] ! {hotel.name} -- {type(exc).__name__}: {exc}"
                ))
                time.sleep(options["sleep"])
                continue

            if photo:
                hotel.external_image_url = photo["url"]
                hotel.save(update_fields=["external_image_url"])
                fetched += 1
                self.stdout.write(f"  [{i}/{total}] OK {hotel.name} -> {photo.get('attribution', 'saved')}")
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i}/{total}] -- {hotel.name} -- no match found on Unsplash or Wikimedia"
                ))
            time.sleep(options["sleep"])

        self.stdout.write(self.style.SUCCESS(
            f"Done. {fetched} fetched, {skipped} no match, {errored} errored (out of {total})."
        ))
        if skipped:
            self.stdout.write(
                "Tip: hotels with no match usually need a more distinctive name "
                "(chain hotels named just 'Hotel Nepal' or similar match poorly) -- "
                "or upload a real photo manually via the admin panel."
            )