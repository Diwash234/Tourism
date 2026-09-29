"""
Management command to generate a revenue report.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
from tourist.models import Booking


class Command(BaseCommand):
    help = "Generate a revenue report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to report on (default: 30)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write("=" * 60)
        self.stdout.write(f"REVENUE REPORT (last {days} days)")
        self.stdout.write("=" * 60)

        if not hasattr(Booking, "objects"):
            self.stdout.write("Booking model not available")
            return

        bookings = Booking.objects.filter(created_at__gte=cutoff)
        total_revenue = bookings.aggregate(total=Sum("total_price"))["total"] or 0
        booking_count = bookings.count()

        self.stdout.write(f"\nTotal bookings: {booking_count}")
        self.stdout.write(f"Total revenue: ${total_revenue:,.2f}")

        if booking_count > 0:
            avg_booking = total_revenue / booking_count
            self.stdout.write(f"Average booking value: ${avg_booking:,.2f}")

        self.stdout.write("\n" + "=" * 60)
