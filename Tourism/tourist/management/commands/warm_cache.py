"""
Management command to warm the cache with frequently accessed data.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from tourist.models import Destination, Category


class Command(BaseCommand):
    help = "Warm the cache with frequently accessed data"

    def handle(self, *args, **options):
        self.stdout.write("Warming cache...")

        # Cache featured destinations
        featured = Destination.objects.filter(is_featured=True, is_published=True)[:10]
        cache.set("featured_destinations", list(featured), timeout=3600)
        self.stdout.write(f"  Cached {len(featured)} featured destinations")

        # Cache categories
        categories = Category.objects.filter(is_active=True)
        cache.set("categories", list(categories), timeout=3600)
        self.stdout.write(f"  Cached {len(categories)} categories")

        # Cache popular destinations
        popular = Destination.objects.filter(is_published=True).order_by("-view_count")[:20]
        cache.set("popular_destinations", list(popular), timeout=3600)
        self.stdout.write(f"  Cached {len(popular)} popular destinations")

        self.stdout.write(self.style.SUCCESS("Cache warming complete"))
