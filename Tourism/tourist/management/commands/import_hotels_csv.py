"""
Offline import of hotels from Tourism/dataset/hotel.csv.

The existing import_hotels command relies on live reverse-geocoding
(Nominatim), which is slow and fails without network. This command reads
the CSV directly, matches each hotel to a Destination by city/destination
name, and assigns a relevant cover image via the photo catalog. It is safe
to re-run: existing hotels (matched by name) are skipped.

Usage:
    python manage.py import_hotels_csv
    python manage.py import_hotels_csv --csv /path/to/hotel.csv
"""
import csv
import os

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.models import Hotel, Destination
from tourist import photo_catalog


class Command(BaseCommand):
    help = "Import hotels from hotel.csv (offline, no geocoding)."

    def add_arguments(self, parser):
        default = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "dataset", "hotel.csv"))
        parser.add_argument("--csv", default=default)

    def handle(self, *args, **options):
        path = options["csv"]
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"CSV not found: {path}"))
            return

        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.stdout.write(f"Loaded {len(rows)} hotels from {os.path.basename(path)}")

        created = 0
        skipped = 0
        for i, row in enumerate(rows, 1):
            name = (row.get("Hotel Name") or "").strip()
            if not name:
                continue
            if Hotel.objects.filter(name__iexact=name).exists():
                skipped += 1
                continue

            city = (row.get("Destination") or "").strip()
            dest = None
            if city:
                dest = (
                    Destination.objects.filter(Q(city__iexact=city) | Q(name__icontains=city)).first()
                    or Destination.objects.filter(Q(district__iexact=city) | Q(province__iexact=city)).first()
                )
            if dest is None:
                dest = Destination.objects.filter(category__name__iexact="hotel").first() \
                    or Destination.objects.first()

            try:
                lat = float(row.get("Latitude")) if row.get("Latitude") else None
                lon = float(row.get("Longitude")) if row.get("Longitude") else None
            except (TypeError, ValueError):
                lat = lon = None

            try:
                rating = float(row.get("Rating")) if row.get("Rating") else None
            except (TypeError, ValueError):
                rating = None
            try:
                price = float(row.get("Price Per Night")) if row.get("Price Per Night") else None
            except (TypeError, ValueError):
                price = None

            photo = photo_catalog.resolve_hotel_photo(
                type("H", (), {"name": name, "id": i})()
            )

            status_map = {
                "available": "available",
                "booked": "booked",
                "closed": "closed",
            }
            booking_status = status_map.get(
                (row.get("Booking Status") or "").strip().lower(), "unknown"
            )

            Hotel.objects.create(
                destination=dest,
                name=name[:200],
                address=(row.get("Address") or "")[:255],
                latitude=lat,
                longitude=lon,
                rating=rating,
                price_per_night=price,
                currency=(row.get("Currency") or "USD")[:10],
                booking_status=booking_status,
                booking_url=(row.get("Booking URL") or "")[:500],
                external_image_url=photo["url"],
                cover_image=photo["url"],
                source="dataset",
            )
            created += 1
            if i % 100 == 0:
                self.stdout.write(f"  [{i}/{len(rows)}] created={created} skipped={skipped}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. created={created} skipped={skipped} total_hotels={Hotel.objects.count()}"
        ))
