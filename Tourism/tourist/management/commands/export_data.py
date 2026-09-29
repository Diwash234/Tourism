"""
Management command to export data in various formats.
"""
import json
import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from tourist.models import Destination, Category, Review, User


class Command(BaseCommand):
    help = "Export tourism data to CSV or JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            type=str,
            choices=["csv", "json"],
            default="json",
            help="Export format",
        )
        parser.add_argument(
            "--model",
            type=str,
            choices=["destinations", "categories", "reviews", "users"],
            default="destinations",
            help="Model to export",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="export",
            help="Output file name (without extension)",
        )

    def handle(self, *args, **options):
        fmt = options["format"]
        model = options["model"]
        output = options["output"]

        self.stdout.write(f"Exporting {model} as {fmt}...")

        if model == "destinations":
            data = list(Destination.objects.values(
                "id", "name", "slug", "description", "district", "province",
                "latitude", "longitude", "is_published", "is_featured",
            ))
        elif model == "categories":
            data = list(Category.objects.values("id", "name", "slug", "is_active"))
        elif model == "reviews":
            data = list(Review.objects.values(
                "id", "user_id", "destination_id", "rating", "comment", "created_at"
            ))
        elif model == "users":
            data = list(User.objects.values(
                "id", "email", "first_name", "last_name", "role", "date_joined"
            ))
        else:
            self.stderr.write(f"Unknown model: {model}")
            return

        output_path = Path(f"{output}.{fmt}")

        if fmt == "json":
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif fmt == "csv":
            if data:
                with open(output_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(data)} records to {output_path}"))
