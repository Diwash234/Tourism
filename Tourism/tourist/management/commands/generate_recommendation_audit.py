"""
Management command to generate a recommendation audit report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, Review


class Command(BaseCommand):
    help = "Generate a recommendation audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("RECOMMENDATION AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Top rated destinations
        self.stdout.write("\nTop Rated Destinations:")
        top_rated = Destination.objects.filter(
            is_published=True,
            average_rating__gt=0,
        ).order_by("-average_rating")[:10]
        for dest in top_rated:
            self.stdout.write(f"  {dest.name} — {dest.average_rating} ({dest.review_count} reviews)")

        # Most reviewed destinations
        self.stdout.write("\nMost Reviewed Destinations:")
        most_reviewed = Destination.objects.filter(
            is_published=True,
        ).order_by("-review_count")[:10]
        for dest in most_reviewed:
            self.stdout.write(f"  {dest.name} — {dest.review_count} reviews")

        self.stdout.write("\n" + "=" * 60)
