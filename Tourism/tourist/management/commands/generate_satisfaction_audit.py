"""
Management command to generate a customer satisfaction audit report.
"""
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from tourist.models import Review


class Command(BaseCommand):
    help = "Generate a customer satisfaction audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CUSTOMER SATISFACTION AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Overall rating
        avg_rating = Review.objects.filter(is_approved=True).aggregate(
            avg=Avg("rating")
        )["avg"] or 0
        self.stdout.write(f"\nOverall average rating: {avg_rating:.2f}/5")

        # Rating distribution
        self.stdout.write("\nRating distribution:")
        ratings = Review.objects.filter(is_approved=True).values("rating").annotate(
            count=Count("id")
        ).order_by("rating")
        for r in ratings:
            self.stdout.write(f"  {r['rating']} stars: {r['count']} reviews")

        # Total reviews
        total = Review.objects.filter(is_approved=True).count()
        self.stdout.write(f"\nTotal approved reviews: {total}")

        self.stdout.write("\n" + "=" * 60)
