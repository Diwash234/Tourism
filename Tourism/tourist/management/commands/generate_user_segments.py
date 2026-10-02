"""
Management command to generate user segments for targeted marketing.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg
from tourist.models import User, Review, Favorite, TravelPlan


class Command(BaseCommand):
    help = "Generate user segments for targeted marketing"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("USER SEGMENTS REPORT")
        self.stdout.write("=" * 60)

        # Active users (logged in last 30 days)
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(days=30)
        active_users = User.objects.filter(last_login__gte=cutoff).count()
        self.stdout.write(f"\nActive users (30d): {active_users}")

        # Power users (5+ reviews)
        power_users = User.objects.annotate(
            review_count=Count("review")
        ).filter(review_count__gte=5).count()
        self.stdout.write(f"Power users (5+ reviews): {power_users}")

        # Travel planners (3+ travel plans)
        planners = User.objects.annotate(
            plan_count=Count("travelplan")
        ).filter(plan_count__gte=3).count()
        self.stdout.write(f"Travel planners (3+ plans): {planners}")

        # Social users (10+ favorites)
        social_users = User.objects.annotate(
            fav_count=Count("favorite")
        ).filter(fav_count__gte=10).count()
        self.stdout.write(f"Social users (10+ favorites): {social_users}")

        # Average reviews per user
        avg_reviews = User.objects.annotate(
            review_count=Count("review")
        ).aggregate(avg=Avg("review_count"))["avg"] or 0
        self.stdout.write(f"\nAverage reviews per user: {avg_reviews:.2f}")

        self.stdout.write("\n" + "=" * 60)
