"""
Management command to generate a maintenance report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, DestinationImage, ErrorEvent


class Command(BaseCommand):
    help = "Generate a maintenance report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("MAINTENANCE REPORT")
        self.stdout.write("=" * 60)

        # Orphaned images
        self.stdout.write("\nOrphaned Images:")
        orphaned = DestinationImage.objects.filter(destination__isnull=True).count()
        self.stdout.write(f"  Orphaned images: {orphaned}")

        # Pending moderation
        self.stdout.write("\nPending Moderation:")
        pending_images = DestinationImage.objects.filter(verification_status="pending").count()
        self.stdout.write(f"  Pending images: {pending_images}")

        # Recent errors
        self.stdout.write("\nRecent Errors (last 7 days):")
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(days=7)
        errors = ErrorEvent.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"  Errors: {errors}")

        self.stdout.write("\n" + "=" * 60)
