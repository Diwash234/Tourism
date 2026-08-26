import json

from django.core.management.base import BaseCommand, CommandError

from tourist.emergency_service import build_emergency_directory, resolve_destination
from tourist.risk_service import build_destination_risk
from tourist.serializers import DestinationListSerializer


PLACES = ["Pokhara", "Kathmandu", "Rara", "Mustang", "Jumla", "Humla", "Chitwan", "Lumbini", "Dhangadhi", "Dadeldhura"]


class Command(BaseCommand):
    help = "Run the Nepal-wide destination/risk/emergency acceptance matrix"

    def handle(self, *args, **options):
        rows, failures, image_urls = [], [], {}
        for query in PLACES:
            destination = resolve_destination(query)
            if not destination:
                failures.append(f"{query}: destination not found"); continue
            if destination.latitude is None or destination.longitude is None:
                failures.append(f"{query}: exact coordinates unavailable"); continue
            serialized = DestinationListSerializer(destination).data
            emergency = build_emergency_directory(
                destination.latitude, destination.longitude, destination=destination,
                radius_km=50, limit=20,
            )
            risk = build_destination_risk(destination)
            image = serialized.get("cover_image_url")
            if image:
                image_urls.setdefault(image, []).append(destination.name)
            rows.append({
                "query": query, "destination": destination.name, "slug": destination.slug,
                "district": destination.district, "province": destination.province,
                "municipality": destination.municipality,
                "coordinates": [float(destination.latitude), float(destination.longitude)],
                "verified_image": image,
                "hospitals_returned": len(emergency["hospitals"]),
                "police_returned": len(emergency["police"]),
                "essentials_returned": len(emergency["specialized_contacts"]),
                "risk_level": risk["overall"]["level"],
                "official_warning": risk["current_conditions"]["official_warning_present"],
                "risk_calculated_at": str(risk["calculated_at"]),
            })
        duplicates = {url: names for url, names in image_urls.items() if len(names) > 1}
        if duplicates:
            failures.append(f"Duplicate verified images: {duplicates}")
        self.stdout.write(json.dumps({"results": rows, "failures": failures}, indent=2, default=str))
        if failures:
            raise CommandError(f"Acceptance check found {len(failures)} issue(s).")
        self.stdout.write(self.style.SUCCESS("Nepal-wide acceptance matrix passed."))
