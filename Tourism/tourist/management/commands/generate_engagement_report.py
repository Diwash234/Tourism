"""
Management command to generate an engagement report.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import User, Review, Favorite, VisitHistory


class Command(BaseCommand):
    help = "Generate an engagement report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to report on (default: 30)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write("=" * 60)
        self.stdout.write(f"ENGAGEMENT REPORT (last {days} days)")
        self.stdout.write("=" * 60)

        # Reviews
        reviews = Review.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"\nReviews created: {reviews}")

        # Favorites
        favorites = Favorite.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"Favorites added: {favorites}")

        # Visit history
        visits = VisitHistory.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"Destinations visited: {visits}")

        # Active users
        active_users = User.objects.filter(last_login__gte=cutoff).count()
        self.stdout.write(f"Active users: {active_users}")

        self.stdout.write("\n" + "=" * 60)
