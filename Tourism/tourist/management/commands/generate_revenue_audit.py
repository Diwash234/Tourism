"""
Management command to generate a revenue audit report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
from tourist.models import Booking


class Command(BaseCommand):
    help = "Generate a revenue audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("REVENUE AUDIT REPORT")
        self.stdout.write("=" * 60)

        if not hasattr(Booking, "objects"):
            self.stdout.write("Booking model not available")
            return

        cutoff = timezone.now() - timedelta(days=30)

        bookings = Booking.objects.filter(created_at__gte=cutoff)
        total_revenue = bookings.aggregate(total=Sum("total_price"))["total"] or 0
        booking_count = bookings.count()

        self.stdout.write(f"\nTotal bookings (30d): {booking_count}")
        self.stdout.write(f"Total revenue (30d): ${total_revenue:,.2f}")

        if booking_count > 0:
            avg_booking = total_revenue / booking_count
            self.stdout.write(f"Average booking value: ${avg_booking:,.2f}")

        self.stdout.write("\n" + "=" * 60)
