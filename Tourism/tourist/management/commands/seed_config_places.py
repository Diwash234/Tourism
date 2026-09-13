"""V6 §2: migrate hardcoded place dictionaries into DB-backed ConfigPlace rows.

Idempotent. Coordinates are copied VERBATIM from the legacy config files
(provenance recorded); nothing is invented. Where an equivalent canonical
Destination already exists (case-insensitive name + district), the row links
to it instead of implying a second identity.

Usage:
    python manage.py seed_config_places [--dry-run]
"""

import json
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from tourist.location.administrative_boundaries import MUNICIPALITY_COORDINATES
from tourist.location.search_service import NEPAL_LANDMARKS
from tourist.models import ConfigPlace, Destination

# Explicit classification only (no fabricated categories).
LANDMARK_CATEGORIES = {
    "phewa lake": "Lakes & Water Activities",
    "fewa lake": "Lakes & Water Activities",
    "pashupatinath": "Temples & Hindu Sites",
    "boudhanath": "Buddhist Sites & Monasteries",
    "swayambhunath": "Buddhist Sites & Monasteries",
    "patan durbar square": "UNESCO & Historical Heritage",
    "bhaktapur durbar square": "UNESCO & Historical Heritage",
    "lumbini": "Pilgrimage Sites",
    "chitwan": "National Park",
    "sarangkot": "Viewpoints & Lookouts",
    "nagarkot": "Viewpoints & Lookouts",
}
DEFAULT_LANDMARK_CATEGORY = "City Tourism"
MUNI_CATEGORY = "City Tourism"


class Command(BaseCommand):
    help = "Seed DB-backed ConfigPlace rows from legacy hardcoded dictionaries (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        stats = {"created": 0, "updated": 0, "linked_existing_destination": 0}
        rows = []
        for key, v in MUNICIPALITY_COORDINATES.items():
            rows.append(dict(
                config_key=f"muni-{key}", kind="municipality_hub",
                name=key.title(), lat=v["lat"], lng=v["lng"],
                district=v.get("district", ""), province=v.get("province", ""),
                city=v.get("district", ""), category_name=MUNI_CATEGORY,
                provenance=f"config:tourist/location/administrative_boundaries.py MUNICIPALITY_COORDINATES, migrated {date.today()}",
            ))
        for key, v in NEPAL_LANDMARKS.items():
            rows.append(dict(
                config_key=f"landmark-{key}", kind="landmark",
                name=v["name"], lat=v["lat"], lng=v["lng"],
                district=v.get("district", ""), province=v.get("province", ""),
                city=v.get("city", ""),
                category_name=LANDMARK_CATEGORIES.get(key, DEFAULT_LANDMARK_CATEGORY),
                provenance=f"config:tourist/location/search_service.py NEPAL_LANDMARKS, migrated {date.today()}",
            ))

        for r in rows:
            # link to an existing canonical Destination when one clearly matches
            link = (Destination.objects
                    .filter(name__iexact=r["name"], district__iexact=r["district"])
                    .exclude(latitude__isnull=True).first())
            if link is None:
                # municipalities: match "<Name> Municipality/Metropolitan City" loosely
                base = r["name"].replace(" Metropolitan City", "").replace(" Municipality", "")
                link = (Destination.objects
                        .filter(name__iexact=base, district__iexact=r["district"])
                        .exclude(latitude__isnull=True).first())
            defaults = dict(
                kind=r["kind"], name=r["name"],
                latitude=Decimal(str(r["lat"])), longitude=Decimal(str(r["lng"])),
                district=r["district"], province=r["province"], city=r["city"],
                category_name=r["category_name"], provenance=r["provenance"],
                linked_destination=link,
            )
            if opts["dry_run"]:
                exists = ConfigPlace.objects.filter(config_key=r["config_key"]).exists()
                stats["created" if not exists else "updated"] += 1
                continue
            obj, created = ConfigPlace.objects.update_or_create(
                config_key=r["config_key"], defaults=defaults)
            stats["created" if created else "updated"] += 1
            if link is not None:
                stats["linked_existing_destination"] += 1

        self.stdout.write(json.dumps(stats, indent=1))
