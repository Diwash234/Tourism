"""
Management command to generate a system health report.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache

from tourist.models import Destination, User, Review, Booking


class Command(BaseCommand):
    help = "Generate a comprehensive system health report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("NEPAL TOURISM PLATFORM — SYSTEM HEALTH REPORT")
        self.stdout.write("=" * 60)

        # Database stats
        self.stdout.write("\n--- Database Statistics ---")
        self.stdout.write(f"  Destinations: {Destination.objects.count()}")
        self.stdout.write(f"  Users: {User.objects.count()}")
        self.stdout.write(f"  Reviews: {Review.objects.count()}")
        self.stdout.write(f"  Bookings: {Booking.objects.count() if hasattr(Booking, 'objects') else 'N/A'}")

        # Database connection
        self.stdout.write("\n--- Database Connection ---")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS("  Database: OK"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  Database: FAILED — {exc}"))

        # Cache
        self.stdout.write("\n--- Cache ---")
        try:
            cache.set("health_check", "ok", 10)
            if cache.get("health_check") == "ok":
                self.stdout.write(self.style.SUCCESS("  Cache: OK"))
            else:
                self.stdout.write(self.style.ERROR("  Cache: FAILED"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  Cache: FAILED — {exc}"))

        # Recent errors
        self.stdout.write("\n--- Recent Errors (last 24h) ---")
        from datetime import timedelta
        from django.utils import timezone
        from tourist.models import ErrorEvent
        recent_errors = ErrorEvent.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        self.stdout.write(f"  Errors in last 24h: {recent_errors}")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("END OF REPORT")
        self.stdout.write("=" * 60)
