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
from tourist.models import Destination, DestinationImage

print("=== Overall coverage ===")
total = Destination.objects.filter(is_active=True).count()
with_img = Destination.objects.filter(is_active=True).annotate(ic=Count("gallery")).filter(ic__gt=0).count()
print(f"Total: {total}")
print(f"With images: {with_img} ({100*with_img//total}%)")
print(f"Without images: {total - with_img}")

print("\n=== Pokhara itinerary destinations ===")
check_names = [
    "Mahendra Cave", "Lakeside", "Boudhanath", "Pumdikot",
    "Davis Falls", "Gupteshwar", "Peace Pagoda", "Sarangkot",
    "Begnas", "Bindhyabasini", "Ghandruk", "Bandipur",
    "Australian Camp", "Dhampus", "Kande", "Birethanti",
]
for name in check_names:
    dests = Destination.objects.filter(name__icontains=name)
    for d in dests[:2]:
        imgs = d.gallery.all()
        img_count = imgs.count()
        # Check if images have external URLs (real) or are local placeholders
        external = sum(1 for i in imgs if i.external_url)
        local = sum(1 for i in imgs if i.image)
        status = "OK" if img_count > 0 else "MISSING"
        print(f"  [{status}] {d.name}: {img_count} images ({external} external, {local} local)")

print("\n=== Image source breakdown ===")
total_imgs = DestinationImage.objects.count()
external = DestinationImage.objects.exclude(external_url="").count()
local = DestinationImage.objects.exclude(image="").count()
print(f"Total destination images: {total_imgs}")
print(f"External URL images: {external}")
print(f"Local file images: {local}")

print("\n=== Sample external URLs (verify they are real) ===")
for img in DestinationImage.objects.exclude(external_url="").order_by("?")[:5]:
    print(f"  {img.destination.name}: {img.external_url[:80]}")
