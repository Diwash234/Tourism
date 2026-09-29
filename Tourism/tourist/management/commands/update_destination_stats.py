"""
Management command to update destination statistics (view counts, ratings, etc.).
"""
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from tourist.models import Destination, Review


class Command(BaseCommand):
    help = "Update destination statistics"

    def handle(self, *args, **options):
        self.stdout.write("Updating destination statistics...")

        destinations = Destination.objects.all()
        updated = 0

        for destination in destinations:
            # Update review count and average rating
            reviews = Review.objects.filter(destination=destination, is_approved=True)
            review_count = reviews.count()
            avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0

            # Update destination fields
            destination.review_count = review_count
            destination.average_rating = round(avg_rating, 2)
            destination.save(update_fields=["review_count", "average_rating", "updated_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated statistics for {updated} destinations"))
