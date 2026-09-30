"""
Management command to generate a user retention report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import User


class Command(BaseCommand):
    help = "Generate a user retention report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("USER RETENTION REPORT")
        self.stdout.write("=" * 60)

        now = timezone.now()

        # Daily active users (last 7 days)
        self.stdout.write("\nDaily Active Users (last 7 days):")
        for i in range(7):
            day = now - timedelta(days=i)
            active = User.objects.filter(
                last_login__date=day.date()
            ).count()
            self.stdout.write(f"  {day.strftime('%Y-%m-%d')}: {active}")

        # Monthly retention
        self.stdout.write("\nMonthly Active Users:")
        for i in range(6):
            month_start = now - timedelta(days=30*i)
            month_end = now - timedelta(days=30*(i-1)) if i > 0 else now
            active = User.objects.filter(
                last_login__gte=month_start,
                last_login__lt=month_end,
            ).count()
            self.stdout.write(f"  {month_start.strftime('%Y-%m')}: {active}")

        self.stdout.write("\n" + "=" * 60)
