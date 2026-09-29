"""
Management command to generate a performance report.
"""
import time
from django.core.management.base import BaseCommand
from django.db import connection
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate a performance report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("PERFORMANCE REPORT")
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

        # Database stats
        self.stdout.write("\nDatabase Statistics:")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tourist_destination")
            count = cursor.fetchone()[0]
            self.stdout.write(f"  Total destinations: {count}")

        self.stdout.write("\n" + "=" * 60)
