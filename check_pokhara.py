import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django

django.setup()

from tourist.models import Destination, Hotel, Hospital
from tourist.utils import haversine_distance

pokhara = Destination.objects.filter(name__icontains="pokhara").first()
print("Pokhara:", pokhara.name if pokhara else "NOT FOUND")

print("\nHospitals within 15km:")
nearby_h = []
for h in Hospital.objects.all():
    if h.latitude and h.longitude and pokhara and pokhara.latitude:
        d = haversine_distance(float(pokhara.latitude), float(pokhara.longitude),
                               float(h.latitude), float(h.longitude))
        if d <= 15:
            nearby_h.append((round(d, 1), h.name, h.phone, h.address))
for d, name, phone, addr in sorted(nearby_h)[:15]:
    print(f"  {d}km | {name} | {phone}")
print(f"  total: {len(nearby_h)}")

print("\nAll destinations with 'pokhara' or 'bandipur' or 'ghandruk' or 'sarangkot':")
for name_q in ["pokhara", "bandipur", "ghandruk", "sarangkot", "begnas", "rupa", "davis", "gupteshwar", "peace pagoda", "pumdikot", "kande", "australian", "dhampus", "bindhyabasini", "birethanti", "nayapul"]:
    found = Destination.objects.filter(name__icontains=name_q).values_list("name", "slug", "latitude", "longitude")[:3]
    if found:
        for n, s, lat, lng in found:
            print(f"  {name_q}: {n} ({s}) [{lat},{lng}]")
