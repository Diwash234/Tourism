from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import DestinationImage


TRUSTED_SEED_SOURCES = {
    DestinationImage.Source.WIKIMEDIA,
    DestinationImage.Source.UNSPLASH,
    DestinationImage.Source.GOOGLE_PLACES,
    DestinationImage.Source.FOURSQUARE,
    DestinationImage.Source.REFERENCE,
    DestinationImage.Source.IMAGE_SERVER,
}


class Command(BaseCommand):
    help = "Make already-approved, externally hosted seed media visible to the public serializers."

    def handle(self, *args, **options):
        qs = DestinationImage.objects.filter(
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=False,
        ).filter(
            source__in=TRUSTED_SEED_SOURCES,
            external_url__gt="",
        )
        total = qs.count()
        if not total:
            self.stdout.write("Public media visibility: no approved seed rows need repair.")
            return
        with transaction.atomic():
            updated = qs.update(is_verified=True)
        self.stdout.write(self.style.SUCCESS(
            f"Public media visibility: promoted {updated} approved externally-hosted seed images."
        ))
