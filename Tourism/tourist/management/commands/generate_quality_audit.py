"""
Management command to generate a quality audit report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, DestinationImage, Review


class Command(BaseCommand):
    help = "Generate a quality audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("QUALITY AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Destinations without images
        no_images = Destination.objects.filter(gallery__isnull=True).count()
        self.stdout.write(f"\nDestinations without images: {no_images}")

        # Destinations without reviews
        no_reviews = Destination.objects.filter(is_published=True).exclude(
            review__isnull=False
        ).count()
        self.stdout.write(f"Destinations without reviews: {no_reviews}")

        # Low rated destinations
        low_rated = Destination.objects.filter(
            is_published=True,
            average_rating__lt=3,
            average_rating__gt=0,
        ).count()
        self.stdout.write(f"Low rated destinations (< 3 stars): {low_rated}")

        # Pending images
        pending_images = DestinationImage.objects.filter(
            verification_status="pending"
        ).count()
        self.stdout.write(f"Pending images: {pending_images}")

        self.stdout.write("\n" + "=" * 60)
