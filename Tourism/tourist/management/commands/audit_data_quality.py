import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.models import Destination, DestinationImage, Hospital, Hotel, OSMEssentialService, PoliceStation


class Command(BaseCommand):
    help = "Audit production data gaps without creating or fabricating replacement records"

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Optional CSV path for destination-level gaps")

    def handle(self, *args, **options):
        approved = Destination.objects.filter(is_active=True, status="approved")
        summary = {
            "approved_destinations": approved.count(),
            "missing_coordinates": approved.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True)).count(),
            "missing_municipality": approved.filter(Q(municipality__isnull=True) | Q(municipality="")).count(),
            "missing_district": approved.filter(Q(district__isnull=True) | Q(district="")).count(),
            "missing_displayable_image": 0,
            "destination_media_rows": DestinationImage.objects.count(),
            "hospitals": Hospital.objects.count(),
            "verified_hospitals": Hospital.objects.filter(is_verified=True).count(),
            "police_stations": PoliceStation.objects.count(),
            "verified_police_stations": PoliceStation.objects.filter(is_verified=True).count(),
            "hotels": Hotel.objects.count(),
            "verified_hotels": Hotel.objects.filter(is_verified=True).count(),
            "essential_services": OSMEssentialService.objects.count(),
            "verified_essential_services": OSMEssentialService.objects.filter(is_verified=True).count(),
        }
        gaps = []
        from tourist.serializers import verified_destination_photos
        for destination in approved.prefetch_related("gallery").iterator(chunk_size=500):
            issues = []
            if destination.latitude is None or destination.longitude is None: issues.append("coordinates")
            if not destination.municipality: issues.append("municipality")
            if not destination.district: issues.append("district")
            if not destination.cover_image and not verified_destination_photos(destination):
                issues.append("displayable_image"); summary["missing_displayable_image"] += 1
            if issues:
                gaps.append({"id": destination.id, "name": destination.name, "district": destination.district or "", "province": destination.province or "", "missing": "|".join(issues)})
        if options.get("output"):
            path = Path(options["output"]); path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "name", "district", "province", "missing"])
                writer.writeheader(); writer.writerows(gaps)
            summary["output"] = str(path)
        summary["destinations_with_gaps"] = len(gaps)
        self.stdout.write(json.dumps(summary, indent=2))
