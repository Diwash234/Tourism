"""
Imports a hotels/accommodation dataset CSV into the Hotel table, linking
each row to an existing Destination by name.

Expected CSV columns:
    destination_name, name, price_per_night, currency, rating,
    booking_status (available|unavailable|unknown), booking_url, address,
    latitude, longitude

Usage:
    python manage.py import_hotels path/to/hotels_dataset.csv
"""
import csv

from django.core.management.base import BaseCommand, CommandError

from tourist.models import Destination, Hotel


class Command(BaseCommand):
    help = "Imports a hotels/accommodation CSV into the Hotel table."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        created, skipped_no_destination = 0, 0

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        destination = Destination.objects.get(name__iexact=row["destination_name"].strip())
                    except Destination.DoesNotExist:
                        skipped_no_destination += 1
                        continue

                    Hotel.objects.update_or_create(
                        destination=destination,
                        name=row["name"].strip(),
                        defaults={
                            "price_per_night": row.get("price_per_night") or None,
                            "currency": row.get("currency") or "USD",
                            "rating": row.get("rating") or None,
                            "booking_status": row.get("booking_status") or Hotel.BookingStatus.UNKNOWN,
                            "booking_url": row.get("booking_url", "").strip(),
                            "address": row.get("address", "").strip(),
                            "latitude": row.get("latitude") or None,
                            "longitude": row.get("longitude") or None,
                            "source": Hotel.Source.DATASET,
                        },
                    )
                    created += 1
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")
        except KeyError as exc:
            raise CommandError(f"Missing required column in CSV: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"Imported/updated {created} hotels, skipped {skipped_no_destination} "
            f"rows with no matching destination."
        ))
