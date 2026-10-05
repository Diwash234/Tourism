import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django

django.setup()

from tourist.models import Destination, DestinationImage

# Check image coverage for key destinations
cities = [
    "Kathmandu", "Pokhara", "Lalitpur", "Bharatpur", "Hetauda",
    "Biratnagar", "Birgunj", "Janakpur", "Nepalgunj", "Butwal",
    "Dharan", "Itahari", "Dhangadhi", "Birendranagar", "Bandipur",
]
print("=== Image coverage ===")
for name in cities:
    dests = Destination.objects.filter(name__icontains=name)
    total_images = 0
    for d in dests:
        total_images += d.gallery.count()
    print(f"  {name}: {dests.count()} destinations, {total_images} images")

# Overall stats
total_dests = Destination.objects.filter(is_active=True).count()
with_images = Destination.objects.filter(is_active=True).exclude(gallery=None).distinct().count()
print(f"\nTotal active destinations: {total_dests}")
print(f"Destinations with images: {with_images}")
print(f"Destinations without images: {total_dests - with_images}")
