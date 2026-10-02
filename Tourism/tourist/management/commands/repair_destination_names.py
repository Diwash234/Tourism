from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination


EXACT_RENAMES = {
    # OSM/third-party import supplied a Korean rendering of this Nepal hotel
    # even though the public Nepal catalogue is maintained in English/Nepali.
    "더 노스 페이스 인": "The North Face Inn",
}


class Command(BaseCommand):
    help = "Repair known non-English imported destination names without changing legitimate Nepali text."

    def handle(self, *args, **options):
        changed = 0
        with transaction.atomic():
            for old, new in EXACT_RENAMES.items():
                rows = list(Destination.objects.filter(name=old))
                for destination in rows:
                    destination.name = new
                    destination.save(update_fields=["name", "updated_at"])
                    changed += 1
        self.stdout.write(self.style.SUCCESS(
            f"Destination name repair: changed={changed}"
        ))
