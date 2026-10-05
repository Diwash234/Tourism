"""Generate travel guides for all 200 Nepal cities from the CSV.

For each city:
- Find or create a Destination record
- Find nearby real hotels, hospitals, attractions from the DB
- Generate a 3-5 day itinerary (shorter for smaller cities)
- Link everything to real data

Run:
    python manage.py seed_all_city_guides
"""
import csv
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from django.core.management.base import BaseCommand

from tourist.models import (
    Destination, Hotel, Hospital, TravelGuide, TravelGuideDay,
)
from tourist.utils import haversine_distance


class Command(BaseCommand):
    help = "Generate travel guides for all 200 Nepal cities."

    def handle(self, *args, **options):
        csv_path = ROOT / "Tourism" / "dataset" / "nepal_cities_200.csv"
        if not csv_path.exists():
            self.stderr.write(f"CSV not found: {csv_path}")
            return

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cities = list(reader)

        self.stdout.write(f"Processing {len(cities)} cities...")

        created_guides = 0
        updated_guides = 0
        skipped = 0

        for i, row in enumerate(cities, 1):
            city_name = row["city"].strip()
            province = row["province"].strip()
            district = row["district"].strip()
            city_type = row.get("type", "").strip()

            # Find or create destination
            dest = Destination.objects.filter(name__icontains=city_name).first()
            if not dest:
                # Create a minimal destination record
                dest = Destination.objects.create(
                    name=city_name,
                    slug=city_name.lower().replace(" ", "-").replace("(", "").replace(")", ""),
                    district=district,
                    province=province,
                    is_active=True,
                    status="approved",
                )

            # Determine itinerary length based on city type
            if city_type == "metropolitan":
                days_count = 7
            elif city_type == "sub-metropolitan":
                days_count = 5
            else:
                days_count = 3

            # Find nearby real data
            hotels = self._get_nearby_hotels(dest, limit=3)
            hospitals = self._get_nearby_hospitals(dest, limit=3)
            attractions = self._get_nearby_attractions(dest, limit=5)

            # Create or update guide
            guide, created = TravelGuide.objects.update_or_create(
                slug=f"{days_count}-day-{dest.slug}",
                defaults={
                    "title": f"{days_count}-Day {city_name} Guide",
                    "subtitle": f"Explore {city_name} and surrounding {district} district in {province}. Real hotels, hospitals and attractions linked.",
                    "destination": dest,
                    "days_count": days_count,
                    "pace": "Relaxed",
                    "best_for": "Couples, families, solo travelers",
                    "is_published": True,
                },
            )
            if created:
                created_guides += 1
            else:
                updated_guides += 1

            # Create days
            self._create_days(guide, dest, city_name, district, province, days_count, hotels, hospitals, attractions)

            if i % 20 == 0:
                self.stdout.write(f"  ... {i}/{len(cities)} cities processed")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created_guides} guides created, {updated_guides} updated, {skipped} skipped."
        ))

    def _get_nearby_hotels(self, dest, limit=3):
        if not dest.latitude or not dest.longitude:
            return []
        lat, lng = float(dest.latitude), float(dest.longitude)
        candidates = Hotel.objects.filter(
            destination__latitude__gte=lat - 0.5,
            destination__latitude__lte=lat + 0.5,
            destination__longitude__gte=lng - 0.5,
            destination__longitude__lte=lng + 0.5,
        ).select_related("destination")
        rows = []
        for h in candidates:
            if h.destination.latitude and h.destination.longitude:
                d = haversine_distance(lat, lng, float(h.destination.latitude), float(h.destination.longitude))
                rows.append((d, h))
        return [h for _, h in sorted(rows, key=lambda x: x[0])[:limit]]

    def _get_nearby_hospitals(self, dest, limit=3):
        if not dest.latitude or not dest.longitude:
            return []
        lat, lng = float(dest.latitude), float(dest.longitude)
        candidates = Hospital.objects.filter(
            latitude__gte=lat - 0.5,
            latitude__lte=lat + 0.5,
            longitude__gte=lng - 0.5,
            longitude__lte=lng + 0.5,
        )
        rows = []
        for h in candidates:
            if h.latitude and h.longitude:
                d = haversine_distance(lat, lng, float(h.latitude), float(h.longitude))
                rows.append((d, h))
        return [h for _, h in sorted(rows, key=lambda x: x[0])[:limit]]

    def _get_nearby_attractions(self, dest, limit=5):
        if not dest.latitude or not dest.longitude:
            return []
        lat, lng = float(dest.latitude), float(dest.longitude)
        candidates = Destination.objects.filter(
            is_active=True,
            latitude__gte=lat - 0.5,
            latitude__lte=lat + 0.5,
            longitude__gte=lng - 0.5,
            longitude__lte=lng + 0.5,
        ).exclude(id=dest.id)
        rows = []
        for a in candidates:
            if a.latitude and a.longitude:
                d = haversine_distance(lat, lng, float(a.latitude), float(a.longitude))
                rows.append((d, a))
        return [a for _, a in sorted(rows, key=lambda x: x[0])[:limit]]

    def _create_days(self, guide, dest, city_name, district, province, days_count, hotels, hospitals, attractions):
        day_templates = [
            {
                "title": f"Arrive in {city_name}",
                "morning": f"Arrive in {city_name}. Check into your hotel. Rest and freshen up.",
                "afternoon": f"Explore {city_name} town center. Visit local markets and try regional cuisine.",
                "evening": f"Sunset walk around {city_name}. Dinner at a local restaurant.",
                "practical_notes": f"{city_name} is in {district} district, {province}. Taxis and local transport are readily available.",
            },
            {
                "title": f"{city_name} Sightseeing",
                "morning": f"Visit the main temples and cultural sites in {city_name}.",
                "afternoon": f"Explore local museums, viewpoints, and historical areas.",
                "evening": f"Shopping for local handicrafts and souvenirs. Dinner at a recommended restaurant.",
                "practical_notes": "Wear comfortable walking shoes. Carry water and sunscreen.",
            },
            {
                "title": f"Nature & Outdoors around {city_name}",
                "morning": f"Day trip to nearby natural attractions — lakes, rivers, viewpoints, or hiking trails.",
                "afternoon": f"Picnic lunch. Photography. Village walks.",
                "evening": f"Return to {city_name}. Relax at the hotel.",
                "practical_notes": "Hire a local guide for hiking. Check weather conditions before departing.",
            },
            {
                "title": f"Cultural Immersion in {city_name}",
                "morning": f"Visit local villages and experience traditional culture.",
                "afternoon": f"Cookery class or craft workshop. Interact with local communities.",
                "evening": f"Cultural performance or local festival if timing aligns.",
                "practical_notes": "Respect local customs. Ask permission before photographing people.",
            },
            {
                "title": f"Adventure Day from {city_name}",
                "morning": f"Adventure activities — paragliding, rafting, zip-lining, or trekking depending on location.",
                "afternoon": f"Continue activities or relax at a café.",
                "evening": f"Celebrate the adventure with a special dinner.",
                "practical_notes": "Book adventure activities through licensed operators. Check safety equipment.",
            },
            {
                "title": f"Day Trip from {city_name}",
                "morning": f"Drive to a nearby destination — another city, national park, or scenic spot.",
                "afternoon": f"Explore the day-trip destination. Lunch there.",
                "evening": f"Drive back to {city_name}. Rest.",
                "practical_notes": "Road travel in Nepal takes longer than map distances suggest. Allow buffer time.",
            },
            {
                "title": f"Final Day in {city_name}",
                "morning": f"Leisurely breakfast. Last-minute shopping. Visit any missed spots.",
                "afternoon": f"Check out. Transfer to airport or bus station.",
                "evening": f"Departure.",
                "practical_notes": "Keep travel insurance and passport copies. Save emergency numbers offline.",
            },
        ]

        for day_num in range(1, days_count + 1):
            template = day_templates[day_num - 1]
            day, _ = TravelGuideDay.objects.update_or_create(
                guide=guide,
                day_number=day_num,
                defaults={
                    "title": template["title"],
                    "morning": template["morning"],
                    "afternoon": template["afternoon"],
                    "evening": template["evening"],
                    "practical_notes": template["practical_notes"],
                    "primary_destination": dest,
                },
            )
            day.hotels.set(hotels)
            day.hospitals.set(hospitals)
            day.attractions.set(attractions)
