"""
Management command to generate a destination report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, DestinationImage, Review


class Command(BaseCommand):
    help = "Generate a destination report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DESTINATION REPORT")
        self.stdout.write("=" * 60)

        total = Destination.objects.count()
        published = Destination.objects.filter(is_published=True).count()
        featured = Destination.objects.filter(is_featured=True).count()

        self.stdout.write(f"\nTotal destinations: {total}")
        self.stdout.write(f"Published: {published}")
        self.stdout.write(f"Featured: {featured}")

        # Destinations without images
        no_images = Destination.objects.filter(gallery__isnull=True).count()
        self.stdout.write(f"\nDestinations without images: {no_images}")

        # Top rated destinations
        self.stdout.write("\nTop rated destinations:")
        top_rated = Destination.objects.filter(
            is_published=True,
            average_rating__gt=0,
        ).order_by("-average_rating")[:10]
        for dest in top_rated:
            self.stdout.write(f"  {dest.name} — {dest.average_rating} ({dest.review_count} reviews)")

        # Most reviewed destinations
        self.stdout.write("\nMost reviewed destinations:")
        most_reviewed = Destination.objects.filter(
            is_published=True,
        ).order_by("-review_count")[:10]
        for dest in most_reviewed:
            self.stdout.write(f"  {dest.name} — {dest.review_count} reviews")

        self.stdout.write("\n" + "=" * 60)
