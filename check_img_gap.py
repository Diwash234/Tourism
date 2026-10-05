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
from tourist.models import Destination

total = Destination.objects.filter(is_active=True).count()
with_img = Destination.objects.filter(is_active=True).annotate(ic=Count("gallery")).filter(ic__gt=0).count()
without = total - with_img
print(f"Total: {total}")
print(f"With images: {with_img} ({100*with_img//total}%)")
print(f"Without images: {without}")

no_img = Destination.objects.filter(is_active=True).annotate(ic=Count("gallery")).filter(ic=0).order_by("name")[:10]
print("\nSample without images:")
for d in no_img:
    lat = d.latitude or "?"
    lng = d.longitude or "?"
    print(f"  {d.name} ({d.district or '?'}) [{lat},{lng}]")
