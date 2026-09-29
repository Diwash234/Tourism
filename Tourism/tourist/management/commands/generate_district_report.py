"""
Management command to generate a district report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate a district report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DISTRICT REPORT")
        self.stdout.write("=" * 60)

        districts = Destination.objects.filter(
            is_published=True
        ).values("district").annotate(
            count=models.Count("id")
        ).order_by("-count")

        self.stdout.write("\nDestinations per district:")
        for dist in districts:
            self.stdout.write(f"  {dist['district']}: {dist['count']} destinations")

        self.stdout.write("\n" + "=" * 60)
