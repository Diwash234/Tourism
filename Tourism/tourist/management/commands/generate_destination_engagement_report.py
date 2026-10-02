"""
Management command to generate a destination engagement report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import Destination, Review, Favorite, VisitHistory


class Command(BaseCommand):
    help = "Generate a destination engagement report"

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
        self.stdout.write(f"DESTINATION ENGAGEMENT REPORT (last {days} days)")
        self.stdout.write("=" * 60)

        # Most visited destinations
        self.stdout.write("\nMost Visited Destinations:")
        visited = VisitHistory.objects.filter(
            created_at__gte=cutoff
        ).values("destination__name").annotate(
            count=models.Count("id")
        ).order_by("-count")[:10]
        for v in visited:
            self.stdout.write(f"  {v['destination__name']}: {v['count']} visits")

        # Most reviewed destinations
        self.stdout.write("\nMost Reviewed Destinations:")
        reviewed = Review.objects.filter(
            created_at__gte=cutoff
        ).values("destination__name").annotate(
            count=models.Count("id")
        ).order_by("-count")[:10]
        for r in reviewed:
            self.stdout.write(f"  {r['destination__name']}: {r['count']} reviews")

        # Most favorited destinations
        self.stdout.write("\nMost Favorited Destinations:")
        favorited = Favorite.objects.filter(
            created_at__gte=cutoff
        ).values("destination__name").annotate(
            count=models.Count("id")
        ).order_by("-count")[:10]
        for f in favorited:
            self.stdout.write(f"  {f['destination__name']}: {f['count']} favorites")

        self.stdout.write("\n" + "=" * 60)
