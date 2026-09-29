"""
Management command to optimize database performance.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Optimize database performance"

    def handle(self, *args, **options):
        self.stdout.write("Optimizing database...")

        with connection.cursor() as cursor:
            # Analyze tables for query planner
            cursor.execute("ANALYZE")
            self.stdout.write(self.style.SUCCESS("  Database analyzed"))

            # Reindex tables
            cursor.execute("REINDEX DATABASE")
            self.stdout.write(self.style.SUCCESS("  Database reindexed"))

        self.stdout.write(self.style.SUCCESS("Database optimization complete"))
