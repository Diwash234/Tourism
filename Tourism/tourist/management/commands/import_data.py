"""
Management command to import data from JSON or CSV files.
"""
import json
import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from tourist.models import Destination, Category


class Command(BaseCommand):
    help = "Import tourism data from JSON or CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            type=str,
            choices=["json", "csv"],
            default="json",
            help="Import format",
        )
        parser.add_argument(
            "--model",
            type=str,
            choices=["destinations", "categories"],
            default="destinations",
            help="Model to import",
        )
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the import file",
        )

    def handle(self, *args, **options):
        fmt = options["format"]
        model = options["model"]
        file_path = Path(options["file"])

        if not file_path.exists():
            self.stderr.write(f"File not found: {file_path}")
            return

        self.stdout.write(f"Importing {model} from {file_path}...")

        if fmt == "json":
            with open(file_path) as f:
                data = json.load(f)
        elif fmt == "csv":
            with open(file_path, newline="") as f:
                reader = csv.DictReader(f)
                data = list(reader)

        if model == "destinations":
            for item in data:
                Destination.objects.update_or_create(
                    slug=item.get("slug"),
                    defaults={
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "district": item.get("district", ""),
                        "province": item.get("province", ""),
                        "latitude": float(item.get("latitude", 0) or 0),
                        "longitude": float(item.get("longitude", 0) or 0),
                    },
                )
        elif model == "categories":
            for item in data:
                Category.objects.update_or_create(
                    slug=item.get("slug"),
                    defaults={
                        "name": item.get("name", ""),
                        "is_active": item.get("is_active", True),
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(data)} records"))
