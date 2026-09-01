"""Fill missing destination city/coords from other recorded destinations.

Does not invent coordinates. Uses:
  1. another destination with the same name that already has coords
  2. the mean of recorded destinations in the same district/city
  3. city from municipality / recorded neighbour (never a district name)
Also writes Tourism/dataset/destination_locations.json so clones can
re-apply the same recorded fields without committing db.sqlite3.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.location_sync import (
    apply_destination_locations,
    export_destination_locations,
    fill_city_from_records,
    fill_coords_from_records,
    fill_ktm_distance,
)
from tourist.models import Destination


class Command(BaseCommand):
    help = "Fill missing destination city/coordinates from other recorded places and export JSON."

    def add_arguments(self, parser):
        parser.add_argument("--no-export", action="store_true", help="Skip writing destination_locations.json")
        parser.add_argument("--no-apply", action="store_true", help="Skip applying destination_locations.json first")

    def handle(self, *args, **options):
        applied = 0
        if not options.get("no_apply"):
            applied = apply_destination_locations()
        filled_coords = 0
        filled_city = 0
        filled_distance = 0
        qs = Destination.objects.filter(is_active=True)

        for dest in (qs.filter(latitude__isnull=True) | qs.filter(longitude__isnull=True)).distinct():
            if fill_coords_from_records(dest):
                dest.save(update_fields=["latitude", "longitude", "updated_at"])
                filled_coords += 1

        for dest in (qs.filter(city__isnull=True) | qs.filter(city="")).distinct():
            if fill_city_from_records(dest):
                dest.save(update_fields=["city", "updated_at"])
                filled_city += 1

        refined_city = 0
        for dest in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            if fill_city_from_records(dest, upgrade=True):
                dest.save(update_fields=["city", "updated_at"])
                refined_city += 1

        for dest in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            if fill_ktm_distance(dest):
                dest.save(update_fields=["distance_from_kathmandu_km", "updated_at"])
                filled_distance += 1

        exported = 0
        if not options.get("no_export"):
            active_count = Destination.objects.filter(is_active=True).count()
            if active_count < 100:
                self.stdout.write("Skipping export: fewer than 100 destinations (likely a test database).")
            else:
                _, exported = export_destination_locations()

        remaining_coords = Destination.objects.filter(is_active=True, latitude__isnull=True).count()
        remaining_city = Destination.objects.filter(is_active=True).filter(
            Q(city__isnull=True) | Q(city="")
        ).count()
        self.stdout.write(self.style.SUCCESS(
            f"Applied JSON={applied}, filled coords={filled_coords}, city={filled_city}, "
            f"refined_city={refined_city}, ktm_distance={filled_distance}, exported={exported}. "
            f"Still missing coords={remaining_coords}, city={remaining_city}."
        ))
