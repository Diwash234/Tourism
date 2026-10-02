"""
Management command to generate a forecast audit report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import Destination, User, Review


class Command(BaseCommand):
    help = "Generate a forecast audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("FORECAST AUDIT REPORT")
        self.stdout.write("=" * 60)

        now = timezone.now()

        # Calculate growth rates
        this_month = now - timedelta(days=30)
        last_month = now - timedelta(days=60)

        users_this = User.objects.filter(date_joined__gte=this_month).count()
        users_last = User.objects.filter(
            date_joined__gte=last_month,
            date_joined__lt=this_month,
        ).count()

        if users_last > 0:
            growth_rate = ((users_this - users_last) / users_last) * 100
            self.stdout.write(f"\nUser growth rate: {growth_rate:.1f}%")
        else:
            self.stdout.write("\nUser growth rate: N/A (no data for last month)")

        # Forecast next month
        if users_last > 0:
            forecast = int(users_this * (1 + growth_rate / 100))
            self.stdout.write(f"Forecast for next month: {forecast} new users")

        self.stdout.write("\n" + "=" * 60)
