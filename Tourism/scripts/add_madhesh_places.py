"""Add Madhesh Province famous named attractions (from the ward-level district
data) as real destinations with categories + coordinates. Skips existing."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

# (name, category_slug, district, province, city, lat, lon, short)
PLACES = [
    # ---------- Saptari ----------
    ("Chandra Nahar", "heritage", "Saptari", "Madhesh", "Fattepur", 26.74, 86.83, "Nepal's first large irrigation canal, a historic engineering heritage of Saptakoshi Municipality."),
    ("Ankuri Mahadev Temple", "temples", "Saptari", "Madhesh", "Ankuri", 26.68, 86.68, "Shiva temple north of the Hanumannagar-Rajbiraj route, a noted Saptari pilgrimage site."),
    ("Rupani Devi Temple", "temples", "Saptari", "Madhesh", "Rupani", 26.62, 86.62, "Goddess temple after which Rupani Rural Municipality is named."),
    ("Dina-Bhadri Baba Temple", "temples", "Saptari", "Madhesh", "Rupani", 26.63, 86.63, "Baba shrine of Rupani Rural Municipality, Saptari."),
    ("Shani Dev Temple Rupani", "temples", "Saptari", "Madhesh", "Rupani", 26.62, 86.64, "Shani temple listed as a tourist place of Rupani, Saptari."),
    ("Khaki Baba Shrine", "pilgrimage", "Saptari", "Madhesh", "Rupani", 26.61, 86.65, "Religious shrine of Rupani Rural Municipality, Saptari."),
    ("Seta Devi Temple", "temples", "Saptari", "Madhesh", "Surunga", 26.60, 86.72, "Goddess temple of Surunga Municipality Ward 4, Saptari."),
    ("Bhediya Children's Park", "parks-gardens", "Saptari", "Madhesh", "Bhediya", 26.61, 86.71, "Recreation park of Surunga Municipality, Saptari."),
    ("Bisnariya Daha", "lakes", "Saptari", "Madhesh", "Surunga", 26.59, 86.70, "Wetland pond of Surunga Municipality, Saptari."),
    ("Musharniya Daha", "lakes", "Saptari", "Madhesh", "Surunga", 26.60, 86.73, "Wetland pond of Surunga Municipality, Saptari."),
    ("Sukhani Martyrs' Site", "heritage", "Jhapa", "Koshi", "Sukhani", 26.65, 87.93, "Memorial site of the martyrs of Arjundhara, Jhapa."),
    # ---------- Dhanusha ----------
    ("Vivah Mandap", "heritage", "Dhanusha", "Madhesh", "Janakpur", 26.729, 85.924, "Sacred pavilion beside Janaki Mandir where Rama-Sita's marriage is celebrated."),
    ("Ganga Sagar Pond", "lakes", "Dhanusha", "Madhesh", "Janakpur", 26.728, 85.927, "One of Janakpur's most sacred ancient ponds."),
    ("Dhanusha Sagar Pond", "lakes", "Dhanusha", "Madhesh", "Janakpur", 26.730, 85.926, "Sacred pond of Janakpur, part of the Mithila religious circuit."),
    ("Parshuram Kunda", "lakes", "Dhanusha", "Madhesh", "Dhanushadham", 26.75, 85.95, "Pond west of Dhanushadham where Parshuram is believed to have bathed."),
    ("Mithila Bihari Mandir", "temples", "Dhanusha", "Madhesh", "Mithila Bihari", 26.83, 85.99, "Temple of Mithila Bihari Bhagwan (Ram), start of the Mithila Madhyama Parikrama."),
    ("Janak Temple", "temples", "Dhanusha", "Madhesh", "Janakpur", 26.731, 85.925, "Temple of King Janak in Janakpur."),
    ("Rangabhoomi", "heritage", "Dhanusha", "Madhesh", "Janakpur", 26.727, 85.923, "Historic grounds in Janakpur associated with Mithila cultural performances."),
    ("Dulha-Dulhan Mandir", "temples", "Dhanusha", "Madhesh", "Janakpur", 26.732, 85.924, "Bride-groom temple of Janakpur, an important Mithila heritage site."),
    ("Parshuram Talau", "lakes", "Dhanusha", "Madhesh", "Mithila Bihari", 26.84, 85.98, "Pond of Mithila Bihari Municipality, Dhanusha."),
    ("Matihani Math", "heritage", "Mahottari", "Madhesh", "Matihani", 26.83, 85.80, "Historic math and religious centre of Matihani, Mahottari."),
    ("Rauja Mazaar", "pilgrimage", "Mahottari", "Madhesh", "Rauja", 26.87, 85.84, "Islamic religious heritage site (mazaar) of Mahottari."),
    # ---------- Sarlahi ----------
    ("Nunthar Pahad", "viewpoints", "Sarlahi", "Madhesh", "Nunthar", 27.18, 85.32, "Hill viewpoint of Sarlahi with views over Makwanpur, Sindhuli and Rautahat."),
    ("Nadiman Lake (Yaksha Kunda)", "lakes", "Sarlahi", "Madhesh", "Nadiman", 27.05, 85.55, "Sacred lake of Sarlahi, also known as Yaksha Kunda."),
    ("Sagaranatha Temple", "temples", "Sarlahi", "Madhesh", "Sagaranath", 27.02, 85.58, "Shiva temple of northern Sarlahi."),
    ("Chaturbhuj Eshwara Temple", "temples", "Sarlahi", "Madhesh", "Chaturbhuj", 27.00, 85.52, "Vishnu temple of Sarlahi district."),
    ("Sarlahi Devi Temple", "temples", "Sarlahi", "Madhesh", "Sarlahi", 26.97, 85.52, "Goddess temple of Sarlahi district."),
    ("Durga Devi Temple Sarlahi", "temples", "Sarlahi", "Madhesh", "Sarlahi", 26.96, 85.53, "Durga temple of Sarlahi district."),
    ("Lalbandi Tomato Region", "agriculture", "Sarlahi", "Madhesh", "Lalbandi", 27.04, 85.48, "Nepal's 'Tomato Capital' - famous agricultural tourism region of Lalbandi."),
    ("Malangwa Baba", "pilgrimage", "Sarlahi", "Madhesh", "Malangwa", 26.87, 85.55, "Religious site of Malangwa, Sarlahi."),
    ("Buddha Park Malangwa", "parks-gardens", "Sarlahi", "Madhesh", "Malangwa", 26.86, 85.56, "Recreation park of Malangwa, Sarlahi."),
    ("Karmaihiya", "villages", "Sarlahi", "Madhesh", "Karmaihiya", 26.90, 85.57, "Cultural/rural tourism village of Sarlahi."),
    # ---------- Rautahat ----------
    ("Paurai Brahmasthal", "pilgrimage", "Rautahat", "Madhesh", "Paurai", 27.09, 85.25, "Historic religious site of Paurai, Rautahat."),
    ("Shivnagar Shiva Temple", "temples", "Rautahat", "Madhesh", "Shivnagar", 27.06, 85.30, "Major Shiva temple of Garuda/Rautahat."),
    ("Nazarpur Krishna Temple", "temples", "Rautahat", "Madhesh", "Nazarpur", 27.03, 85.28, "Krishna temple (Nijanandadham) of Rautahat."),
    ("Matsari Durga Temple", "temples", "Rautahat", "Madhesh", "Matsari", 27.02, 85.32, "Durga temple of Rautahat district."),
    ("Mardhar Simsar Wetland", "lakes", "Rautahat", "Madhesh", "Santapur", 27.00, 85.26, "Wetland of Santapur, an emerging Rautahat nature destination."),
    ("Barahwa Wetland Gaur", "lakes", "Rautahat", "Madhesh", "Gaur", 26.96, 85.27, "Wetland near Gaur, Rautahat."),
    ("Junge Jharana", "waterfalls", "Rautahat", "Madhesh", "Hattidamadar", 27.15, 85.18, "Waterfall in the Hattidamadar forest, about 16 km west of Nunthar."),
    ("Purenawa Palace", "heritage", "Rautahat", "Madhesh", "Purenawa", 27.05, 85.23, "Historic palace of Rautahat district."),
    ("Pataura Historical Temple", "temples", "Rautahat", "Madhesh", "Pataura", 27.04, 85.24, "Historic temple of Rautahat."),
    ("Shahid Smriti Park", "parks-gardens", "Rautahat", "Madhesh", "Gaur", 26.97, 85.28, "Martyrs' memorial park of Gaur, Rautahat."),
    ("Tileshwor Park", "parks-gardens", "Rautahat", "Madhesh", "Tileshwor", 26.98, 85.29, "Recreation park of Rautahat."),
    # ---------- Bara ----------
    ("Kankali Temple Simraungadh", "temples", "Bara", "Madhesh", "Simraungadh", 26.90, 85.10, "Goddess temple of the medieval Simraungadh heritage complex."),
    ("Raniwas Temple", "heritage", "Bara", "Madhesh", "Simraungadh", 26.90, 85.11, "Historic palace-temple of Simraungadh."),
    ("Deutal Pond", "lakes", "Bara", "Madhesh", "Simraungadh", 26.91, 85.09, "Historic sacred pond of Simraungadh."),
    ("Hariharpur Pillar", "heritage", "Bara", "Madhesh", "Simraungadh", 26.89, 85.12, "Archaeological pillar of Simraungadh, linked to the Karnat dynasty."),
    ("Baba Parasnath", "pilgrimage", "Bara", "Madhesh", "Simraungadh", 26.90, 85.08, "Religious site of Simraungadh."),
    ("Kamaleshwarnath Mahadev", "temples", "Bara", "Madhesh", "Simraungadh", 26.91, 85.10, "Shiva temple of Simraungadh."),
    ("Simraungadh Kotwali", "heritage", "Bara", "Madhesh", "Simraungadh", 26.90, 85.11, "Historic kotwali (fort/guard post) of Simraungadh."),
    ("Amlekhganj", "cities", "Bara", "Madhesh", "Amlekhganj", 27.28, 84.98, "Historic railway town and Chure gateway of Bara district."),
    ("Pathlaiya", "cities", "Bara", "Madhesh", "Pathlaiya", 27.37, 85.00, "Highway junction town of Bara district."),
    ("Jitpur", "cities", "Bara", "Madhesh", "Jitpur", 27.13, 84.99, "Urban centre of Jitpur-Simara sub-metropolitan city."),
    ("Simara Airport", "heritage", "Bara", "Madhesh", "Simara", 27.16, 84.98, "Regional airport of Jitpur-Simara, Bara."),
    # ---------- Parsa ----------
    ("Ghadiarwa Pokhari", "lakes", "Parsa", "Madhesh", "Birgunj", 27.01, 84.87, "Major urban pond and Chhath recreation area of Birgunj."),
    ("Gahawa Mai Temple", "temples", "Parsa", "Madhesh", "Birgunj", 27.00, 84.87, "Goddess temple of Birgunj."),
    ("Maisthan Temple", "temples", "Parsa", "Madhesh", "Birgunj", 27.01, 84.88, "Religious site of Birgunj."),
    ("Thori", "villages", "Parsa", "Madhesh", "Thori", 27.27, 84.82, "Village on the southern edge of Parsa National Park, a wildlife-tourism gateway."),
    ("Kailash Bhata", "temples", "Parsa", "Madhesh", "Parsa National Park", 27.42, 84.88, "Religious hill inside Parsa National Park with views over the Terai forest."),
    ("Parsagadhi Temple", "temples", "Parsa", "Madhesh", "Parsagadhi", 27.16, 84.92, "Historic temple of Parsagadhi Municipality."),
    ("Koilabhar Temple", "temples", "Parsa", "Madhesh", "Parsagadhi", 27.15, 84.93, "Temple of Parsagadhi Municipality."),
    ("Bahudarmai Temple", "temples", "Parsa", "Madhesh", "Bahudarmai", 27.06, 84.90, "Goddess temple of Bahudarmai Municipality Ward 2, with the Shesh Nag shrine."),
    ("Pokhariya", "cities", "Parsa", "Madhesh", "Pokhariya", 27.03, 84.85, "Town and municipality of Parsa district."),
    ("Jagarnathpur", "cities", "Parsa", "Madhesh", "Jagarnathpur", 26.99, 84.92, "Town of Parsa district."),
    ("Adhabar", "villages", "Parsa", "Madhesh", "Adhabar", 27.23, 84.90, "Village access point of Parsa National Park."),
    ("Birgunj Ghantaghar", "heritage", "Parsa", "Madhesh", "Birgunj", 27.005, 84.868, "Iconic clock tower of Birgunj."),
]

created = 0
skipped = 0
for name, cslug, dist, prov, city, lat, lon, short in PLACES:
    slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "").replace("'", "").replace("&", "and").replace("--", "-")
    if Destination.objects.filter(slug=slug).exists():
        skipped += 1
        continue
    cat = cats.get(cslug) or cats.get("attraction")
    Destination.objects.create(
        name=name, slug=slug, category=cat, district=dist, province=prov,
        city=city, city_english=city, latitude=lat, longitude=lon,
        short_description=short, description=short, country="Nepal",
        status="approved", is_active=True, source="madhesh-province-round", views_count=0,
    )
    created += 1

print(f"created: {created} | skipped (already exist): {skipped}")
