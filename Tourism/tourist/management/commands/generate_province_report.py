"""
Management command to generate a province report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate a province report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("PROVINCE REPORT")
        self.stdout.write("=" * 60)

        provinces = Destination.objects.filter(
            is_published=True
        ).values("province").annotate(
            count=models.Count("id")
        ).order_by("-count")

        self.stdout.write("\nDestinations per province:")
        for prov in provinces:
            self.stdout.write(f"  {prov['province']}: {prov['count']} destinations")

        self.stdout.write("\n" + "=" * 60)
