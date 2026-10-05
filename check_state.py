import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django

django.setup()

from django.db.models import Count
from tourist.models import Destination, DestinationImage, TravelGuide, Hotel, Hospital

print("=== Destination image coverage ===")
total = Destination.objects.filter(is_active=True).count()
with_images = Destination.objects.filter(is_active=True).exclude(gallery=None).distinct().count()
without = total - with_images
print(f"Total active destinations: {total}")
print(f"With images: {with_images} ({100*with_images//total}%)")
print(f"Without images: {without} ({100*without//total}%)")

print("\n=== Top 15 destinations by image count ===")
top = Destination.objects.filter(is_active=True).annotate(
    img_count=Count("gallery")
).order_by("-img_count")[:15]
for d in top:
    print(f"  {d.name}: {d.img_count} images")

print("\n=== Destinations with 0 images (sample) ===")
no_img = Destination.objects.filter(is_active=True).annotate(
    img_count=Count("gallery")
).filter(img_count=0).order_by("name")[:20]
for d in no_img:
    print(f"  {d.name} ({d.district or '?'})")

print("\n=== Hotels image coverage ===")
hotels_total = Hotel.objects.count()
hotels_with_img = Hotel.objects.exclude(cover_image="").exclude(cover_image=None).count()
print(f"Hotels: {hotels_with_img}/{hotels_total} with cover images")

print("\n=== Hospitals image coverage ===")
hosp_total = Hospital.objects.count()
hosp_with_img = Hospital.objects.exclude(image="").exclude(image=None).count()
print(f"Hospitals: {hosp_with_img}/{hosp_total} with images")

print("\n=== Travel guides ===")
guides = TravelGuide.objects.filter(is_published=True)
print(f"Published guides: {guides.count()}")
for g in guides[:5]:
    print(f"  {g.title} ({g.days_count} days) - {g.destination.name}")

print("\n=== Destinations with invalid coordinates ===")
invalid = Destination.objects.filter(is_active=True).exclude(
    latitude__isnull=False, longitude__isnull=False
).filter(latitude=0, longitude=0).count()
print(f"Destinations at (0,0): {invalid}")

print("\n=== Destinations missing district ===")
no_district = Destination.objects.filter(is_active=True).filter(district="").count()
print(f"Destinations without district: {no_district}")
