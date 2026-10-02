"""
Management command to update destination statistics (view counts, ratings, etc.).
"""
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from tourist.models import Destination, Rating


class Command(BaseCommand):
    help = "Update destination statistics"

    def handle(self, *args, **options):
        self.stdout.write("Updating destination statistics...")

        destinations = Destination.objects.all()
        updated = 0

        for destination in destinations:
            # Destination has no `review_count` column and Review has no
            # `rating` column -- the 1-5 score lives on Rating.value, so the
            # cache is refreshed from there. (The old Review/is_approved query
            # raised FieldError and crashed this command outright.)
            ratings = Rating.objects.filter(destination=destination)
            avg_rating = ratings.aggregate(avg=Avg("value"))["avg"] or 0

            # Update destination fields
            destination.average_rating = round(avg_rating, 2)
            destination.ratings_count = ratings.count()
            destination.save(update_fields=["average_rating", "ratings_count", "updated_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated statistics for {updated} destinations"))
