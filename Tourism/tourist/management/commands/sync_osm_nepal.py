"""
Syncs OSM essential services + tourism places for a set of Nepal locations.

Usage:
    python manage.py sync_osm_nepal
    python manage.py sync_osm_nepal --radius-m 8000
"""
from django.core.management.base import BaseCommand

from tourist.services.overpass import sync_essential_services, sync_tourism_places

NEPAL_LOCATIONS = [
    ("Kathmandu", 27.7172, 85.3240),
    ("Pokhara", 28.2096, 83.9856),
    ("Chitwan", 27.5291, 84.3542),
    ("Mustang", 28.9977, 83.8460),
    ("Lumbini", 27.4833, 83.2767),
    ("Everest / Solukhumbu", 27.9881, 86.9250),
]


class Command(BaseCommand):
    help = "Syncs OSM essential services and tourism places for Nepal's major tourism areas."

    def add_arguments(self, parser):
        parser.add_argument("--radius-m", type=int, default=5000)

    def handle(self, *args, **options):
        radius_m = options["radius_m"]
        for name, lat, lon in NEPAL_LOCATIONS:
            self.stdout.write(f"Syncing {name}...")
            es_created, es_updated = sync_essential_services(lat, lon, radius_m)
            tp_created, tp_updated = sync_tourism_places(lat, lon, radius_m)
            self.stdout.write(
                f"  Essential services: {es_created} created, {es_updated} updated | "
                f"Tourism places: {tp_created} created, {tp_updated} updated"
            )
        self.stdout.write(self.style.SUCCESS("Done."))
