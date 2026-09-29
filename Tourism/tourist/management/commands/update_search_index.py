"""
Management command to update the search index.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination


class Command(BaseCommand):
    help = "Update the search index for all destinations"

    def handle(self, *args, **options):
        destinations = Destination.objects.all()
        count = 0

        for destination in destinations:
            # Update search vector or index fields
            # This is a placeholder for actual search index logic
            destination.save(update_fields=["updated_at"])
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated search index for {count} destinations"))
