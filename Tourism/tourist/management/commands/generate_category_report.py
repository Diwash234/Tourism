"""
Management command to generate a category report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Category, Destination


class Command(BaseCommand):
    help = "Generate a category report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CATEGORY REPORT")
        self.stdout.write("=" * 60)

        categories = Category.objects.all()
        self.stdout.write(f"\nTotal categories: {categories.count()}")

        self.stdout.write("\nDestinations per category:")
        for category in categories:
            count = Destination.objects.filter(category=category).count()
            published = Destination.objects.filter(
                category=category,
                is_published=True,
            ).count()
            self.stdout.write(f"  {category.name}: {count} total, {published} published")

        self.stdout.write("\n" + "=" * 60)
