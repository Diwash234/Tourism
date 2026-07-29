"""
Backfills a real cover image for every destination that doesn't have one
yet, using the existing ensure_cover_photo() pipeline (Unsplash, then
Wikimedia Commons fallback) in Tourism/tourist/utils.py.

Why this is needed: ensure_cover_photo() already exists and already works,
but it only ever runs lazily -- once, the first time a single destination
is serialized. Nothing has ever looped over ALL destinations, so most of
them still have no cover_image_url, and the frontend falls back to the
same generic Unsplash stock photo for every single card. Running this
command once (and again after any bulk import) gives every destination
its own real, cached photo.

Usage:
    python manage.py backfill_destination_images
    python manage.py backfill_destination_images --limit 50   # test run
"""
import sys
import time

from django.core.management.base import BaseCommand

from tourist.models import Destination
from tourist.utils import ensure_cover_photo


class Command(BaseCommand):
    help = "Fetch and cache a cover photo (Unsplash/Wikimedia) for every destination missing one."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=None,
            help="Only process this many destinations (useful for a test run before UNSPLASH_ACCESS_KEY is confirmed working).",
        )
        parser.add_argument(
            "--sleep", type=float, default=0.5,
            help="Seconds to sleep between destinations, to stay well under Unsplash/Wikimedia rate limits (default 0.5s).",
        )

    def handle(self, *args, **options):
        # Windows consoles default to cp1252, which can raise
        # UnicodeEncodeError on destination names with non-ASCII characters
        # (Nepali place names, accented characters, etc.) and silently kill
        # a run partway through. Force UTF-8 output as a safety net.
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass  # older Python without reconfigure(); safe to ignore
        queryset = Destination.objects.filter(cover_image="").exclude(
            id__in=Destination.objects.exclude(gallery=None).values("id")
        )
        # Simpler/safer: just take destinations with no cover_image AND no gallery rows at all.
        queryset = Destination.objects.filter(cover_image="")
        queryset = [d for d in queryset if not d.gallery.exists()]

        if options["limit"]:
            queryset = queryset[: options["limit"]]

        total = len(queryset)
        self.stdout.write(f"Found {total} destination(s) with no photo at all.")

        fetched, skipped, errored = 0, 0, 0
        for i, destination in enumerate(queryset, start=1):
            try:
                photo = ensure_cover_photo(destination)
            except Exception as exc:  # noqa: BLE001 -- deliberately broad: one bad
                # destination must never kill a 5000+ item run. Log it and move on.
                errored += 1
                self.stdout.write(self.style.ERROR(
                    f"  [{i}/{total}] ! {destination.name} -- {type(exc).__name__}: {exc}"
                ))
                time.sleep(options["sleep"])
                continue

            if photo:
                fetched += 1
                self.stdout.write(f"  [{i}/{total}] OK {destination.name} -> {photo.source}")
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i}/{total}] -- {destination.name} -- no match found on Unsplash or Wikimedia"
                ))
            time.sleep(options["sleep"])

        self.stdout.write(self.style.SUCCESS(
            f"Done. {fetched} fetched, {skipped} no match, {errored} errored (out of {total})."
        ))
        if skipped:
            self.stdout.write(
                "Tip: destinations with no match usually need a more specific name/city "
                "(e.g. 'International Mountain Museum' + city 'Pokhara' matches better than "
                "the name alone) -- or upload a real photo for those manually via the admin panel."
            )