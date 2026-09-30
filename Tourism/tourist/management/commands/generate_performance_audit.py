"""
Management command to generate a performance audit report.
"""
import time
from django.core.management.base import BaseCommand
from django.db import connection
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate a performance audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("PERFORMANCE AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Query performance
        self.stdout.write("\nQuery Performance:")

        start = time.time()
        list(Destination.objects.all()[:100])
        elapsed = time.time() - start
        self.stdout.write(f"  List 100 destinations: {elapsed:.3f}s")

        start = time.time()
        list(Destination.objects.select_related("category").all()[:100])
        elapsed = time.time() - start
        self.stdout.write(f"  List 100 with category: {elapsed:.3f}s")

        start = time.time()
        list(Destination.objects.filter(is_published=True)[:100])
        elapsed = time.time() - start
        self.stdout.write(f"  Filter 100 published: {elapsed:.3f}s")

        # Database stats
        self.stdout.write("\nDatabase Statistics:")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tourist_destination")
            count = cursor.fetchone()[0]
            self.stdout.write(f"  Total destinations: {count}")

        # Recommendations
        self.stdout.write("\nRecommendations:")
        self.stdout.write("  - Add database indexes for frequently queried fields")
        self.stdout.write("  - Use select_related() for foreign key relationships")
        self.stdout.write("  - Use prefetch_related() for many-to-many relationships")
        self.stdout.write("  - Cache frequently accessed data")
        self.stdout.write("  - Paginate large querysets")

        self.stdout.write("\n" + "=" * 60)
