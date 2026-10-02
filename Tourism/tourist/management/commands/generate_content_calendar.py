"""
Management command to generate a content calendar for the next 30 days.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import Destination, Alert


class Command(BaseCommand):
    help = "Generate a content calendar for the next 30 days"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CONTENT CALENDAR (Next 30 Days)")
        self.stdout.write("=" * 60)

        today = timezone.now().date()

        # Seasonal events (Nepal-specific)
        events = {
            0: "New Year's Day",
            1: "Republic Day",
            14: "Maha Shivaratri",
            25: "Holi (Festival of Colors)",
            45: "Nepali New Year",
            120: "Dashain Festival",
            150: "Tihar (Festival of Lights)",
            200: "Buddha Jayanti",
            250: "Teej Festival",
            300: "Indra Jatra",
            350: "Mani Rimdu",
        }

        self.stdout.write("\nUpcoming content opportunities:")
        for day, event in events.items():
            event_date = today + timedelta(days=day)
            self.stdout.write(f"  {event_date.strftime('%Y-%m-%d')}: {event}")

        # Destination highlights
        self.stdout.write("\nDestination highlights:")
        featured = Destination.objects.filter(is_featured=True)[:5]
        for dest in featured:
            self.stdout.write(f"  - {dest.name} ({dest.district})")

        # Active alerts
        self.stdout.write("\nActive alerts:")
        alerts = Alert.objects.filter(is_active=True)[:5]
        for alert in alerts:
            self.stdout.write(f"  - {alert.title} ({alert.severity})")

        self.stdout.write("\n" + "=" * 60)
