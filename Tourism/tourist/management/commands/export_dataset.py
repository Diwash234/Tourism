"""
Exports the current Destination table (plus aggregated review/rating data)
as a CSV — hand this to the ML teammate to retrain the recommendation/
safety/budget models on real data instead of the current CSV snapshot.

Usage:
    python manage.py export_dataset dataset_export.csv
"""
import csv

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count

from tourist.models import Destination


class Command(BaseCommand):
    help = "Exports destinations (with aggregated ratings) to CSV for ML training."

    def add_arguments(self, parser):
        parser.add_argument("output_path", type=str, default="dataset_export.csv", nargs="?")

    def handle(self, *args, **options):
        output_path = options["output_path"]
        qs = Destination.objects.filter(is_active=True).select_related("category").annotate(
            review_count=Count("reviews"),
        )

        fields = [
            "id", "name", "category", "description", "latitude", "longitude",
            "city", "country", "entry_fee", "average_rating", "ratings_count",
            "review_count", "views_count",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for dest in qs.iterator():
                writer.writerow({
                    "id": dest.id, "name": dest.name, "category": dest.category.name,
                    "description": dest.description, "latitude": dest.latitude, "longitude": dest.longitude,
                    "city": dest.city, "country": dest.country, "entry_fee": dest.entry_fee,
                    "average_rating": dest.average_rating, "ratings_count": dest.ratings_count,
                    "review_count": dest.review_count, "views_count": dest.views_count,
                })

        self.stdout.write(self.style.SUCCESS(f"Exported {qs.count()} destinations to {output_path}"))
