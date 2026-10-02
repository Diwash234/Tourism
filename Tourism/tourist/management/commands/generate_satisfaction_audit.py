"""
Management command to generate a customer satisfaction audit report.
"""
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from tourist.models import Rating, Review


class Command(BaseCommand):
    help = "Generate a customer satisfaction audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CUSTOMER SATISFACTION AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Overall rating -- Review is text-only (moderation_status, no numeric
        # rating / is_approved); the 1-5 score lives on Rating.value.
        avg_rating = Rating.objects.aggregate(avg=Avg("value"))["avg"] or 0
        self.stdout.write(f"\nOverall average rating: {avg_rating:.2f}/5")

        # Rating distribution
        self.stdout.write("\nRating distribution:")
        ratings = Rating.objects.values("value").annotate(
            count=Count("id")
        ).order_by("value")
        for r in ratings:
            self.stdout.write(f"  {r['value']} stars: {r['count']} ratings")

        # Total reviews
        total = Review.objects.filter(moderation_status="approved").count()
        self.stdout.write(f"\nTotal approved reviews: {total}")

        self.stdout.write("\n" + "=" * 60)
