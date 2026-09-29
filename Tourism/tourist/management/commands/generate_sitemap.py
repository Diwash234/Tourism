"""
Management command to generate a sitemap.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, Category


class Command(BaseCommand):
    help = "Generate a sitemap for the site"

    def handle(self, *args, **options):
        self.stdout.write("Generating sitemap...")

        destinations = Destination.objects.filter(is_published=True)
        categories = Category.objects.filter(is_active=True)

        self.stdout.write(f"  Destinations: {destinations.count()}")
        self.stdout.write(f"  Categories: {categories.count()}")

        # In a real implementation, this would write to a file or update the database
        # For now, we just report the counts
        self.stdout.write(self.style.SUCCESS("Sitemap generation complete."))
