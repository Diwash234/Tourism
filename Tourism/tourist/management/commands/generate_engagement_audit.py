"""
Management command to generate an engagement audit report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import User, Review, Favorite, VisitHistory


class Command(BaseCommand):
    help = "Generate an engagement audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("ENGAGEMENT AUDIT REPORT")
        self.stdout.write("=" * 60)

        cutoff = timezone.now() - timedelta(days=30)

        # Reviews
        reviews = Review.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"\nReviews created (30d): {reviews}")

        # Favorites
        favorites = Favorite.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"Favorites added (30d): {favorites}")

        # Visits
        visits = VisitHistory.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"Destinations visited (30d): {visits}")

        # Active users
        active_users = User.objects.filter(last_login__gte=cutoff).count()
        self.stdout.write(f"Active users (30d): {active_users}")

        # Engagement rate
        total_users = User.objects.count()
        engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
        self.stdout.write(f"\nEngagement rate: {engagement_rate:.1f}%")

        self.stdout.write("\n" + "=" * 60)
