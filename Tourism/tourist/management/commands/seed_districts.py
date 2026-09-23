"""
seed_districts — idempotent seed for Nepal's administrative geography.

Seeds the 7 provinces and all 77 districts from
`tourist/administrative_boundaries.py` (public administrative facts:
province assignment, headquarters-region note, centre coordinates,
elevation). Safe to run repeatedly: provinces/districts are matched by
slug and existing rows are updated, never duplicated.

Deliberately does NOT seed tourism descriptions, hotels, hospitals or
opening hours — those must come from verified sources (admin entries,
imports, discovery pipeline). Empty description fields are rendered as
"Information unavailable" by the API, never as fabricated text.

Usage:  python manage.py seed_districts
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tourist.administrative_boundaries import NEPAL_DISTRICTS_DATA, NEPAL_PROVINCES
from tourist.models import District, Province


class Command(BaseCommand):
    help = "Idempotently seed Nepal's 7 provinces and 77 districts."

    def handle(self, *args, **options):
        created_p = updated_p = 0
        for row in NEPAL_PROVINCES:
            slug = slugify(row["name"])
            province, created = Province.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": row["name"],
                    "capital": row.get("capital", ""),
                    "order": row.get("id", 0),
                },
            )
            created_p += created
            updated_p += not created

        created_d = updated_d = 0
        for name, info in NEPAL_DISTRICTS_DATA.items():
            province = Province.objects.filter(name=info["province"]).first()
            if province is None:
                self.stderr.write(f"Skipping {name}: unknown province {info['province']!r}")
                continue
            _, created = District.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "province": province,
                    "region_type": info.get("type", ""),
                    "latitude": info.get("lat"),
                    "longitude": info.get("lng"),
                    "elevation_m": info.get("altitude"),
                },
            )
            created_d += created
            updated_d += not created

        self.stdout.write(
            self.style.SUCCESS(
                f"Provinces: {created_p} created, {updated_p} updated. "
                f"Districts: {created_d} created, {updated_d} updated. "
                f"Totals now: {Province.objects.count()} provinces, {District.objects.count()} districts."
            )
        )
