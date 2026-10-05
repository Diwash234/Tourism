import csv, yaml, pathlib, os, sys, django

# Ensure the Django project package (Tourism/) is importable regardless of the
# directory the script is invoked from.
sys.path.insert(0, r"C:\Users\ADMIN\Desktop\Chatbot\Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()
from tourist.models import Destination, Hotel, Hospital, DestinationImage

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\Chatbot")
CSV = ROOT / "Tourism" / "dataset" / "nepal_cities_200.csv"
YAML = ROOT / "Tourism" / "dataset" / "nepal_city_itineraries_200.yaml"

def plain(value):
    """Coerce Django/Python objects into plain YAML-safe scalars.

    ImageFieldFile, Decimal and friends are not representable by
    yaml.safe_load, so the generated file would be unreadable on the next run.
    """
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


rows = list(csv.DictReader(CSV.open(newline='', encoding='utf-8')))
out = yaml.safe_load(YAML.read_text(encoding='utf-8')) if YAML.exists() else {}
cities = out.get('cities', [])

# Build quick lookup of destinations by city name for matching
all_dest = list(Destination.objects.all())
by_city = {}
for d in all_dest:
    # index by normalized city english / name
    for key in filter(None, [d.city_english, d.name]):
        norm = key.lower().strip()
        if norm and norm not in by_city:
            by_city[norm] = d

for row in rows:
    city_name = row['city']
    norm = city_name.lower().strip()
    dest = by_city.get(norm)
    entry = next((c for c in cities if c.get('city') == city_name), None)
    if entry is None:
        entry = {'city': city_name, 'province': row['province'], 'district': row['district']}
        cities.append(entry)
    if dest is None:
        continue
    entry['destination_id'] = dest.id
    entry['destination_slug'] = dest.slug
    entry['destination'] = {
        'name': plain(dest.name),
        'province': plain(dest.province),
        'district': plain(dest.district),
        'description': plain(dest.description or dest.short_description or '')[:400],
        'latitude': float(dest.latitude) if dest.latitude is not None else None,
        'longitude': float(dest.longitude) if dest.longitude is not None else None,
        'cover_image': plain(dest.cover_image) if dest.cover_image else None,
        'nearest_hotel_info': plain(dest.nearest_hotel_info),
        'nearest_hospital_info': plain(dest.nearest_hospital_info),
        'distance_from_kathmandu_km': plain(dest.distance_from_kathmandu_km),
        'nearest_airport_name': plain(dest.nearest_airport_name),
    }
    entry['images'] = []
    for img in dest.gallery.all()[:5]:
        url = img.external_url or img.image
        if url:
            entry['images'].append({
                'url': plain(url),
                'alt': plain(img.alt_text),
                'caption': plain(img.caption),
            })
    hotels = [plain(h.name) for h in dest.hotels.all()[:5]]
    if hotels:
        entry['hotels'] = hotels
    hospitals = [plain(h.name) for h in dest.hospitals.all()[:5]]
    if hospitals:
        entry['hospitals'] = hospitals
    # The live DB already carries a nearest hotel/hospital for every
    # destination; keep it so the dataset always has a usable pointer even
    # when no hotel/hospital is directly attached to this city row.
    if not hotels and entry['destination'].get('nearest_hotel_info'):
        entry['nearest_hotel_info'] = entry['destination']['nearest_hotel_info']
    if not hospitals and entry['destination'].get('nearest_hospital_info'):
        entry['nearest_hospital_info'] = entry['destination']['nearest_hospital_info']

out['cities'] = cities
YAML.write_text(yaml.dump(out, sort_keys=False, allow_unicode=True), encoding='utf-8')
print('Updated', YAML, 'cities', len(cities))
