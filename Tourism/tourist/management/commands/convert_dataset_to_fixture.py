#!/usr/bin/env python
"""Convert dataset/data.json to Django fixture format for PostgreSQL seeding."""
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Convert dataset/data.json to Django fixture format (load.json)"

    # Destination and DestinationImage both inherit TimeStampedModel, whose
    # created_at/updated_at are auto_now fields. loaddata saves with raw=True,
    # so Django does not fill those columns in - the fixture has to provide real
    # timestamps or every insert fails with a NOT NULL constraint violation.
    # The dataset always carries updated_at; this only guards a partial file.
    FALLBACK_TIMESTAMP = "2026-01-01T00:00:00+00:00"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            default="dataset/data.json",
            help="Path to the input JSON file",
        )
        parser.add_argument(
            "--output",
            default="load.json",
            help="Path to the output fixture file",
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        input_path = base_dir / options["input"]
        output_path = base_dir / options["output"]

        if not input_path.is_file():
            self.stdout.write(self.style.ERROR(f"Input file not found: {input_path}"))
            return

        self.stdout.write(f"Reading {input_path}...")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        destinations = data.get("destinations", {})
        if isinstance(destinations, list):
            destinations = {str(item.get("id")): item for item in destinations if item.get("id") is not None}
        self.stdout.write(f"Found {len(destinations)} destinations")

        # Convert to Django fixture format
        fixture = []
        for dest_id, dest_data in destinations.items():
            timestamp = (
                dest_data.get("created_at")
                or dest_data.get("updated_at")
                or self.FALLBACK_TIMESTAMP
            )
            fixture.append({
                "model": "tourist.destination",
                "pk": dest_data["id"],
                "fields": {
                    "name": dest_data["name"],
                    "slug": dest_data["slug"],
                    "city": dest_data.get("city", ""),
                    "city_english": dest_data.get("city_english", ""),
                    "city_nepali": dest_data.get("city_nepali", ""),
                    "district": dest_data.get("district", ""),
                    "province": dest_data.get("province", ""),
                    "municipality": dest_data.get("municipality", ""),
                    "ward_number": dest_data.get("ward_number"),
                    "latitude": dest_data.get("latitude"),
                    "longitude": dest_data.get("longitude"),
                    "distance_from_kathmandu_km": dest_data.get("distance_from_kathmandu_km"),
                    "description": dest_data.get("description", ""),
                    "short_description": dest_data.get("short_description", ""),
                    "status": dest_data.get("status", "approved"),
                    "created_at": timestamp,
                    "updated_at": dest_data.get("updated_at") or timestamp,
                },
            })

            # Add images. The photo URL belongs in external_url: DestinationImage
            # has no "image_url" field, and loaddata rejects unknown fields.
            for img in dest_data.get("images", []):
                img_timestamp = img.get("created_at") or timestamp
                fixture.append({
                    "model": "tourist.destinationimage",
                    "pk": img["id"],
                    "fields": {
                        "destination": dest_data["id"],
                        "external_url": img["url"],
                        "caption": img.get("caption", ""),
                        "is_cover": img.get("is_cover", False),
                        # DestinationImage has no "status" column; review state
                        # lives in verification_status (approved/pending/rejected).
                        "verification_status": img.get("status", "approved"),
                        "created_at": img_timestamp,
                        "updated_at": img.get("updated_at") or img_timestamp,
                    },
                })

        self.stdout.write(f"Writing {len(fixture)} records to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(fixture, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Done! Fixture saved to {output_path}"))
