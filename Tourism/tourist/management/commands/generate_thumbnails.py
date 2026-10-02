"""
Management command to generate thumbnails for destination images.
"""
from django.core.management.base import BaseCommand
from tourist.models import DestinationImage


class Command(BaseCommand):
    help = "Generate thumbnails for destination images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        images = DestinationImage.objects.filter(thumbnail__isnull=True)
        count = images.count()

        self.stdout.write(f"Found {count} images without thumbnails")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made"))
            return

        # In a real implementation, this would use Pillow to generate thumbnails
        self.stdout.write(self.style.SUCCESS(f"Would generate thumbnails for {count} images"))
        self.stdout.write(self.style.WARNING("This feature requires Pillow to be installed"))
