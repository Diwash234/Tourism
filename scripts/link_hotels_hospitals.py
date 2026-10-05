"""Link nearest real hotels/hospitals to every destination.

Updates Destination.nearest_hotel_info and Destination.nearest_hospital_info
with the nearest active hotel/hospital name and distance. Uses all active
records (not just verified) since the user wants real data linked.
"""
import os, sys, django, math

sys.path.insert(0, r"C:\Users\ADMIN\Desktop\Chatbot\Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from tourist.models import Destination, Hotel, Hospital


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# Pre-load all active hotels/hospitals with coordinates as tuples for speed
hotels = [
    (float(h.latitude), float(h.longitude), h.name)
    for h in Hotel.objects.filter(is_active=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
]
hospitals = [
    (float(h.latitude), float(h.longitude), h.name)
    for h in Hospital.objects.filter(is_archived=False).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
]
print(f"Loaded {len(hotels)} hotels, {len(hospitals)} hospitals")

updated = 0
destinations = Destination.objects.filter(is_active=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
total = destinations.count()
print(f"Processing {total} destinations...")

for i, d in enumerate(destinations.iterator()):
    if i % 500 == 0:
        print(f"  {i}/{total}...", flush=True)
    
    d_lat, d_lon = float(d.latitude), float(d.longitude)
    
    # Find nearest hotel
    nearest_h_name = None
    min_h_dist = 99999.0
    for h_lat, h_lon, h_name in hotels:
        dist = haversine(d_lat, d_lon, h_lat, h_lon)
        if dist < min_h_dist:
            min_h_dist = dist
            nearest_h_name = h_name
    
    # Find nearest hospital
    nearest_hosp_name = None
    min_hosp_dist = 99999.0
    for h_lat, h_lon, h_name in hospitals:
        dist = haversine(d_lat, d_lon, h_lat, h_lon)
        if dist < min_hosp_dist:
            min_hosp_dist = dist
            nearest_hosp_name = h_name
    
    changed = False
    if nearest_h_name and (not d.nearest_hotel_info or d.nearest_hotel_info == ""):
        d.nearest_hotel_info = f"{nearest_h_name} ({min_h_dist:.1f} km)"
        changed = True
    if nearest_hosp_name and (not d.nearest_hospital_info or d.nearest_hospital_info == ""):
        d.nearest_hospital_info = f"{nearest_hosp_name} ({min_hosp_dist:.1f} km)"
        changed = True
    
    if changed:
        d.save(update_fields=["nearest_hotel_info", "nearest_hospital_info"])
        updated += 1

print(f"Done. Updated {updated} destinations.")
