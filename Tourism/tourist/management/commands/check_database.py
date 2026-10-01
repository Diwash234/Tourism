"""
Management command to check database health and statistics.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count

from tourist.models import User, Destination, Review, TravelPlan, Booking


class Command(BaseCommand):
    help = "Check database health and statistics"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DATABASE HEALTH CHECK")
        self.stdout.write("=" * 60)

        # Check database connection
        self.stdout.write("\nDatabase Connection:")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS("  Status: OK"))
        except Exception as exc:
            self.stderr.write(f"  Status: ERROR - {exc}")
            return

        # Table statistics
        self.stdout.write("\nTable Statistics:")
        tables = [
            ("Users", User),
            ("Destinations", Destination),
            ("Reviews", Review),
            ("Travel Plans", TravelPlan),
            ("Bookings", Booking),
        ]

        for name, model in tables:
            try:
                count = model.objects.count()
                self.stdout.write(f"  {name}: {count:,} records")
            except Exception as exc:
                self.stderr.write(f"  {name}: ERROR - {exc}")

        # Check for orphaned records
        self.stdout.write("\nOrphaned Records Check:")
        try:
            orphaned_reviews = Review.objects.filter(destination__isnull=True).count()
            self.stdout.write(f"  Reviews without destination: {orphaned_reviews}")
        except Exception as exc:
            self.stderr.write(f"  Error checking reviews: {exc}")

        try:
            orphaned_plans = TravelPlan.objects.filter(user__isnull=True).count()
            self.stdout.write(f"  Travel plans without user: {orphaned_plans}")
        except Exception as exc:
            self.stderr.write(f"  Error checking travel plans: {exc}")

        # Check for duplicate emails
        self.stdout.write("\nDuplicate Check:")
        try:
            duplicate_emails = User.objects.values('email').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            if duplicate_emails:
                self.stdout.write(self.style.WARNING(f"  Duplicate emails found: {duplicate_emails.count()}"))
            else:
                self.stdout.write("  No duplicate emails")
        except Exception as exc:
            self.stderr.write(f"  Error checking duplicate emails: {exc}")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Health check completed")
        self.stdout.write("=" * 60)
