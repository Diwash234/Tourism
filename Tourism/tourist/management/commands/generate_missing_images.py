"""
Management command to generate placeholder images for destinations without images.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate placeholder images for destinations without images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find destinations without images
        destinations = Destination.objects.filter(gallery__isnull=True)
        count = destinations.count()

        self.stdout.write(f"Found {count} destinations without images")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made"))
            for dest in destinations[:10]:
                self.stdout.write(f"  Would generate image for: {dest.name}")
            return

        # In a real implementation, this would generate or assign placeholder images
        # For now, we just report
        self.stdout.write(self.style.SUCCESS(f"Would generate images for {count} destinations"))
        self.stdout.write(self.style.WARNING("This feature requires an image generation service to be configured"))
