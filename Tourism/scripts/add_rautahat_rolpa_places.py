"""Gap-fill the last two districts (Rautahat, Rolpa) with real, verifiable
places so all 77 districts have records, following the same convention as
add_gapfill_places.py / add_sudurpashchim_places.py: curated real place
names, honest minimal descriptions, approximate coordinates rounded to
~1 km. No superlatives, no invented amenities.

Run: python manage.py shell < scripts/add_rautahat_rolpa_places.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from tourist.models import Category, Destination  # noqa: E402
from tourist.location.administrative_boundaries import NEPAL_DISTRICTS  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

PROVINCE_BY_DISTRICT = {"Rautahat": "Madhesh", "Rolpa": "Lumbini"}

# (name, category_slug, district, city, lat, lon, description)
PLACES = [
    # Rautahat (Madhesh) — district HQ Gaur on the Nepal-India border
    ("Rajdevi Mandir Gaur", "temples", "Rautahat", "Gaur", 26.769, 85.273,
     "Hindu temple of Goddess Rajdevi in Gaur, the district headquarters of Rautahat."),
    ("Gaur", "cities", "Rautahat", "Gaur", 26.768, 85.272,
     "District headquarters town of Rautahat on the India-Nepal border, connected to India via the Nagar–Gaur crossing."),
    ("Chandrapur", "cities", "Rautahat", "Chandrapur", 27.288, 85.372,
     "Market town and municipality of Rautahat along the east–west highway corridor."),
    ("Garuda Bazaar", "cities", "Rautahat", "Garuda", 26.946, 85.323,
     "Market town of Garuda municipality in Rautahat."),
    # Rolpa (Lumbini) — district HQ Liwang in the mid-hills
    ("Liwang", "cities", "Rolpa", "Liwang", 28.273, 82.756,
     "District headquarters town of Rolpa at the confluence area of the Runti Khola."),
    ("Runtigadhi", "heritage", "Rolpa", "Liwang", 28.316, 82.628,
     "Ruined hilltop fort-palace of the historical Runti kingdom in western Rolpa."),
    ("Thawang", "villages", "Rolpa", "Thawang", 28.383, 82.921,
     "Village in northern Rolpa known as a base of the People's War (1996–2006)."),
    ("Jaljala", "mountains", "Rolpa", "Jaljala", 28.421, 83.013,
     "Highland area of Jaljala in northern Rolpa, a Magar settlement region with Himalayan views."),
]

created = skipped = 0
for name, cslug, district, city, lat, lon, desc in PLACES:
    cat = cats.get(cslug)
    if not cat:
        print("MISSING CATEGORY", cslug)
        continue
    if Destination.objects.filter(name=name, district=district).exists():
        skipped += 1
        continue
    prov = PROVINCE_BY_DISTRICT[district]
    Destination.objects.create(
        name=name, category=cat, district=district, city_english=city,
        latitude=lat, longitude=lon, short_description=desc,
        description=desc, province=prov,
        status="approved", is_active=True,
    )
    created += 1

canon = set(d for lst in NEPAL_DISTRICTS.values() for d in lst)
covered = set(Destination.objects.exclude(district="").values_list("district", flat=True).distinct())
print(f"created={created} skipped={skipped}")
print("districts covered:", len(canon & covered), "of 77")
print("still empty:", sorted(canon - covered))
