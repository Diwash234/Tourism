"""
Management command to generate an SEO audit report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate an SEO audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SEO AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Check for missing meta descriptions
        no_desc = Destination.objects.filter(
            is_published=True,
            description__isnull=True,
        ).count()
        self.stdout.write(f"\nDestinations without description: {no_desc}")

        # Check for short descriptions
        short_desc = Destination.objects.filter(
            is_published=True,
            description__length__lt=50,
        ).count()
        self.stdout.write(f"Destinations with short descriptions: {short_desc}")

        # Check for missing slugs
        no_slug = Destination.objects.filter(
            is_published=True,
            slug__isnull=True,
        ).count()
        self.stdout.write(f"Destinations without slug: {no_slug}")

        self.stdout.write("\n" + "=" * 60)
