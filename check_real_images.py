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
from tourist.models import Destination, DestinationImage, Hotel

print("=== Image coverage ===")
total = Destination.objects.filter(is_active=True).count()
with_img = Destination.objects.filter(is_active=True).annotate(ic=Count("gallery")).filter(ic__gt=0).count()
print(f"Total destinations: {total}")
print(f"With images: {with_img} ({100*with_img//total}%)")
print(f"Without images: {total - with_img}")

print("\n=== Specific destination image check ===")
check_names = [
    "Mahendra Cave", "Lakeside", "Buddha Stupa", "Boudhanath", "Pumdikot",
    "Davis Falls", "Gupteshwar", "Peace Pagoda", "Sarangkot", "Begnas",
    "Bindhyabasini", "Ghandruk", "Bandipur", "Australian Camp", "Dhampus",
]
for name in check_names:
    dests = Destination.objects.filter(name__icontains=name)
    for d in dests[:2]:
        imgs = d.gallery.all()
        img_count = imgs.count()
        # Check if images have external URLs (real) or are local placeholders
        external = sum(1 for i in imgs if i.external_url)
        local = sum(1 for i in imgs if i.image)
        print(f"  {d.name}: {img_count} images ({external} external, {local} local)")

print("\n=== Hotel image check ===")
hotels_total = Hotel.objects.count()
hotels_with_img = Hotel.objects.exclude(cover_image="").exclude(cover_image=None).count()
print(f"Hotels: {hotels_with_img}/{hotels_total} with cover images")

# Sample hotel images
print("\nSample hotel images:")
for h in Hotel.objects.exclude(cover_image="").exclude(cover_image=None)[:5]:
    print(f"  {h.name}: {h.cover_image}")

print("\n=== Image source breakdown ===")
total_imgs = DestinationImage.objects.count()
external = DestinationImage.objects.exclude(external_url="").count()
local = DestinationImage.objects.exclude(image="").count()
print(f"Total destination images: {total_imgs}")
print(f"External URL images: {external}")
print(f"Local file images: {local}")
