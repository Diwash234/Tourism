import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/home/user/Tourism/Tourism')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
django.setup()

from tourist.models import Destination, Hospital, PoliceStation, Hotel
from tourist.administrative_boundaries import NEPAL_DISTRICTS_DATA

def run():
    print("--- Checking and fixing all destinations missing coordinates or province ---")

    # 1. Fix missing lat/lng
    no_coords = Destination.objects.filter(latitude__isnull=True)
    print(f"Destinations missing coordinates: {no_coords.count()}")
    for d in no_coords:
        dist_info = NEPAL_DISTRICTS_DATA.get(d.district)
        if dist_info:
            d.latitude = dist_info['lat']
            d.longitude = dist_info['lng']
            d.save()
            print(f"[FIXED COORDS] {d.name} ({d.district}) -> ({d.latitude}, {d.longitude})")
        else:
            matches = Destination.objects.filter(district__iexact=d.district, latitude__isnull=False).exclude(id=d.id)
            if matches.exists():
                ref = matches.first()
                d.latitude = ref.latitude
                d.longitude = ref.longitude
                d.save()
                print(f"[FIXED COORDS MATCH] {d.name} ({d.district}) -> ({d.latitude}, {d.longitude})")
            else:
                d.latitude = 27.7172
                d.longitude = 85.3240
                d.save()
                print(f"[FIXED COORDS KATMANDU] {d.name} -> (27.7172, 85.3240)")

    # Build district-to-province mapping from NEPAL_DISTRICTS_DATA
    district_to_province = {}
    for dist_name, dist_info in NEPAL_DISTRICTS_DATA.items():
        prov = dist_info.get("province", "")
        if prov and not prov.endswith("Province"):
            prov = f"{prov} Province"
        district_to_province[dist_name.lower()] = prov

    # 2. Fix missing province
    no_province = Destination.objects.filter(province='')
    print(f"Destinations missing province: {no_province.count()}")
    fixed_prov_count = 0
    for d in no_province:
        dist_key = (d.district or "").strip().lower()
        prov = district_to_province.get(dist_key, "")
        if not prov and dist_key:
            for dk, p in district_to_province.items():
                if dk in dist_key or dist_key in dk:
                    prov = p
                    break
        if not prov:
            prov = "Bagmati Province"
        d.province = prov
        d.save()
        fixed_prov_count += 1

    print(f"Fixed province for {fixed_prov_count} destinations.")

    # 3. Ensure 100% of approved destinations have non-empty district and province
    missing_dist_or_prov = Destination.objects.filter(status='approved').filter(django.db.models.Q(district='') | django.db.models.Q(province=''))
    print(f"Remaining approved destinations missing district or province: {missing_dist_or_prov.count()}")

if __name__ == "__main__":
    run()
