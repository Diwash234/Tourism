"""
Management command to generate a complete system overview.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from tourist.models import Destination, User, Review, Booking, AuditLog, ErrorEvent


class Command(BaseCommand):
    help = "Generate a complete system overview"

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("NEPAL TOURISM PLATFORM — SYSTEM OVERVIEW")
        self.stdout.write("=" * 70)

        # Application info
        self.stdout.write("\n--- Application Info ---")
        self.stdout.write("  Name: Nepal Tourism Platform")
        self.stdout.write("  Version: 1.0.0")
        self.stdout.write("  Framework: Django 6.0")

        # Database stats
        self.stdout.write("\n--- Database Statistics ---")
        self.stdout.write(f"  Destinations: {Destination.objects.count()}")
        self.stdout.write(f"  Users: {User.objects.count()}")
        self.stdout.write(f"  Reviews: {Review.objects.count()}")
        self.stdout.write(f"  Bookings: {Booking.objects.count() if hasattr(Booking, 'objects') else 'N/A'}")
        self.stdout.write(f"  Audit Logs: {AuditLog.objects.count()}")
        self.stdout.write(f"  Error Events: {ErrorEvent.objects.count()}")

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

        # Recent activity
        self.stdout.write("\n--- Recent Activity (last 24h) ---")
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(hours=24)
        new_users = User.objects.filter(date_joined__gte=cutoff).count()
        active_users = User.objects.filter(last_login__gte=cutoff).count()
        new_reviews = Review.objects.filter(created_at__gte=cutoff).count()
        errors = ErrorEvent.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"  New users: {new_users}")
        self.stdout.write(f"  Active users: {active_users}")
        self.stdout.write(f"  New reviews: {new_reviews}")
        self.stdout.write(f"  Errors: {errors}")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("END OF SYSTEM OVERVIEW")
        self.stdout.write("=" * 70)
