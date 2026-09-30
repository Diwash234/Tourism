"""
Management command to generate a trend analysis audit report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import Destination, Review, User


class Command(BaseCommand):
    help = "Generate a trend analysis audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("TREND ANALYSIS AUDIT REPORT")
        self.stdout.write("=" * 60)

        now = timezone.now()

        # User growth trend
        self.stdout.write("\nUser Growth Trend:")
        for i in range(6):
            month_start = now - timedelta(days=30*i)
            month_end = now - timedelta(days=30*(i-1)) if i > 0 else now
            new_users = User.objects.filter(
                date_joined__gte=month_start,
                date_joined__lt=month_end,
            ).count()
            self.stdout.write(f"  {month_start.strftime('%Y-%m')}: +{new_users} users")

        # Review trend
        self.stdout.write("\nReview Trend:")
        for i in range(6):
            month_start = now - timedelta(days=30*i)
            month_end = now - timedelta(days=30*(i-1)) if i > 0 else now
            reviews = Review.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).count()
            self.stdout.write(f"  {month_start.strftime('%Y-%m')}: {reviews} reviews")

        self.stdout.write("\n" + "=" * 60)
