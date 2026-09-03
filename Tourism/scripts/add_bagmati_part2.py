"""Round 17: Add the remaining Bagmati Province famous places (Makwanpur,
Chitwan, Dhading, Nuwakot, Rasuwa) as real destinations with categories +
coordinates. Skips existing (name + district alias), disambiguates slug
collisions, fixes missing district/province on matched rows.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

DISTRICT_ALIASES = {
    "Makwanpur": {"Makwanpur", "मकवानपुर", "मकवानपुर जिल्ला", "Makwanpur District"},
    "Chitwan": {"Chitwan", "Citwan", "चितवन", "चितवन जिल्ला", "Chitwan District"},
    "Dhading": {"Dhading", "धादिङ", "धादिङ जिल्ला", "Dhading District"},
    "Nuwakot": {"Nuwakot", "नुवाकोट", "नुवाकोट जिल्ला", "Nuwakot District"},
    "Rasuwa": {"Rasuwa", "रसुवा", "रसुवा जिल्ला", "Rasuwa District"},
}

# (name, category_slug, district, city, lat, lon, short_description)
PLACES = [
    # ================= MAKWANPUR DISTRICT =================
    ("Hetauda", "cities", "Makwanpur", "Hetauda", 27.428, 85.032, "Industrial capital of Bagmati Province and district headquarters of Makwanpur."),
    ("Chitlang", "villages", "Makwanpur", "Thaha", 27.637, 85.180, "Historic Newar village on the old Kathmandu-Hetauda trail, famous for goat cheese and organic farms."),
    ("Daman", "viewpoints", "Makwanpur", "Thaha", 27.601, 85.058, "Hill station on the Tribhuvan Highway with panoramic Himalayan views."),
    ("Sim Bhangyang", "villages", "Makwanpur", "Thaha", 27.612, 85.090, "Village on the historic Kathmandu-Hetauda trade route."),
    ("Kulekhani Dam", "heritage", "Makwanpur", "Indra Sarobar", 27.583, 85.155, "Dam of Nepal's first storage-type hydroelectric project, creating the Indra Sarobar reservoir."),
    ("Indra Sarobar Lake", "lakes", "Makwanpur", "Indra Sarobar", 27.588, 85.165, "Reservoir lake of Kulekhani, a boating and picnic destination."),
    ("Palung", "villages", "Makwanpur", "Thaha", 27.626, 85.145, "Village on the Tribhuvan Highway near Daman."),
    ("Tistung", "villages", "Makwanpur", "Thaha", 27.618, 85.125, "Hill village of Thaha municipality, Makwanpur."),
    ("Phaparbari", "villages", "Makwanpur", "Manahari", 27.480, 84.990, "Village of Manahari rural municipality, Makwanpur."),
    ("Manahari", "villages", "Makwanpur", "Manahari", 27.463, 84.945, "Village of Makwanpur near the Chitwan border."),
    ("Bhainse", "villages", "Makwanpur", "Bhimphedi", 27.533, 85.115, "Village of Bhimphedi rural municipality, Makwanpur."),
    # ================= CHITWAN DISTRICT =================
    ("Chitwan National Park", "national-park", "Chitwan", "Sauraha", 27.500, 84.330, "UNESCO World Heritage national park of Chitwan, home to the one-horned rhino and Bengal tiger."),
    ("Sauraha", "villages", "Chitwan", "Ratnanagar", 27.578, 84.494, "Gateway tourist town of Chitwan National Park on the Rapti river."),
    ("Bishazari Tal", "lakes", "Chitwan", "Ratnanagar", 27.608, 84.425, "Wetland of twenty lakes near Chitwan National Park, a Ramsar site and birdwatching paradise."),
    ("Elephant Breeding Centre", "wildlife", "Chitwan", "Ratnanagar", 27.575, 84.490, "Government elephant breeding and training centre at Khorsor, Sauraha."),
    ("Gharial Breeding Centre", "wildlife", "Chitwan", "Ratnanagar", 27.582, 84.505, "Breeding centre for the critically endangered gharial crocodile at the park headquarters."),
    ("Tharu Cultural Museum", "museums", "Chitwan", "Ratnanagar", 27.577, 84.493, "Museum of Tharu culture, art and traditions at Sauraha."),
    ("Kasara Durbar", "heritage", "Chitwan", "Ratnanagar", 27.545, 84.340, "Historic Rana hunting palace inside Chitwan National Park, now a museum."),
    ("Meghauli", "villages", "Chitwan", "Kalika", 27.575, 84.250, "Village on the Narayani river in western Chitwan, known for riverside resorts and bird life."),
    ("Devghat", "pilgrimage", "Chitwan", "Devghat", 27.754, 84.425, "Sacred confluence of the Trishuli and Kali Gandaki rivers, a major Hindu pilgrimage town."),
    ("Valmiki Ashram", "pilgrimage", "Chitwan", "Devghat", 27.760, 84.430, "Ashram at Devghat associated with the sage Valmiki, author of the Ramayana."),
    ("Someshwor Hill", "viewpoints", "Chitwan", "Someshwor", 27.633, 84.607, "Hill of eastern Chitwan with the Someshwor Shiva temple and valley views."),
    ("Kumroj", "villages", "Chitwan", "Khairhani", 27.600, 84.480, "Community-forest buffer-zone village of Chitwan known for birdwatching."),
    ("Ratnanagar", "cities", "Chitwan", "Ratnanagar", 27.610, 84.480, "Municipality town serving as the main gateway to Sauraha."),
    ("Bharatpur", "cities", "Chitwan", "Bharatpur", 27.683, 84.432, "Largest city of Chitwan, a major commercial centre of central Nepal."),
    ("Narayanghat", "cities", "Chitwan", "Bharatpur", 27.700, 84.430, "Historic bazaar at the Narayani river crossing, a major transport junction."),
    ("Narayani River", "rivers", "Chitwan", "Bharatpur", 27.690, 84.420, "Major river of Chitwan formed by the Trishuli and Kali Gandaki, western boundary of the national park."),
    ("Rapti River", "rivers", "Chitwan", "Ratnanagar", 27.590, 84.470, "River along the northern boundary of Chitwan National Park, famous for elephant safaris."),
    ("Siraichuli", "viewpoints", "Chitwan", "Ichchhakamana", 27.740, 84.790, "Hill viewpoint of Chitwan with sunrise over the Himalaya and the national park."),
    ("Bhandara", "villages", "Chitwan", "Devghat", 27.748, 84.437, "Village near Devghat famous for community homestays."),
    # ================= DHADING DISTRICT =================
    ("Dhading Besi", "cities", "Dhading", "Dhadingbesi", 27.869, 84.905, "District headquarters town of Dhading."),
    ("Gajuri", "cities", "Dhading", "Gajuri", 27.756, 84.752, "Town of Dhading on the Prithvi Highway."),
    ("Jibjibe", "villages", "Dhading", "Gajuri", 27.737, 84.742, "Road junction town of Dhading."),
    ("Ruby Valley", "valleys", "Dhading", "Rubi Valley", 28.083, 85.000, "Highland valley of northern Dhading traversed by the Ruby Valley trek."),
    ("Tipling", "villages", "Dhading", "Rubi Valley", 28.123, 84.983, "Village of the Ruby Valley trek."),
    ("Somdang Mines", "heritage", "Dhading", "Rubi Valley", 28.167, 84.967, "Historic silver and lead mines visited on the Ruby Valley trek."),
    ("Jharlang", "villages", "Dhading", "Rubi Valley", 28.098, 85.083, "Village on the Ruby Valley trek route."),
    ("Shertung", "villages", "Dhading", "Rubi Valley", 28.142, 85.033, "Village of the Ruby Valley trek."),
    ("Brabal", "villages", "Dhading", "Rubi Valley", 28.113, 84.950, "Village of the Ruby Valley trek."),
    ("Lapa", "villages", "Dhading", "Rubi Valley", 28.078, 84.938, "Village of the Ruby Valley trek."),
    ("Maidi", "villages", "Dhading", "Dhunibeshi", 27.790, 84.868, "Village of Dhunibeshi municipality, Dhading."),
    ("Dhunibesi", "cities", "Dhading", "Dhunibeshi", 27.812, 84.890, "Town of Dhading near the Trishuli river."),
    ("Benighat", "villages", "Dhading", "Benighat Rorang", 27.745, 84.810, "Historic bazaar and river crossing on the old Dhading route."),
    # ================= NUWAKOT DISTRICT =================
    ("Nuwakot Bhairabi Temple", "temples", "Nuwakot", "Nuwakot", 27.914, 85.164, "Goddess temple beside Nuwakot Durbar."),
    ("Nuwakot Taleju Temple", "temples", "Nuwakot", "Nuwakot", 27.913, 85.165, "Taleju temple of the Nuwakot palace complex."),
    ("Trishuli Bazaar", "cities", "Nuwakot", "Trishuli", 27.920, 85.147, "Rafting hub town on the Trishuli river in Nuwakot."),
    ("Betrawati Hot Springs", "hot-springs", "Nuwakot", "Betrawati", 27.943, 85.207, "Hot springs of Betrawati village on the Trishuli river."),
    ("Bidur", "cities", "Nuwakot", "Bidur", 27.885, 85.137, "Municipality town and administrative centre of Nuwakot district."),
    ("Batar Si", "villages", "Nuwakot", "Kispang", 27.988, 85.298, "Village of Nuwakot famous for its dairy and cheese tradition."),
    ("Trishuli River", "rivers", "Nuwakot", "Trishuli", 27.930, 85.155, "Major river of Nuwakot famous for rafting and the Trishuli hydropower cascade."),
    # ================= RASUWA DISTRICT =================
    ("Langtang National Park", "national-park", "Rasuwa", "Langtang", 28.180, 85.550, "National park protecting the Langtang valley, Gosaikunda and the Ganesh Himal."),
    ("Langtang Village", "villages", "Rasuwa", "Langtang", 28.205, 85.570, "Tamang village of the Langtang valley, rebuilt after the 2015 earthquake."),
    ("Dhunche", "cities", "Rasuwa", "Dhunche", 28.110, 85.300, "District headquarters of Rasuwa on the Trishuli highway."),
    ("Syabrubesi", "villages", "Rasuwa", "Syabrubesi", 28.155, 85.350, "Gateway village of the Langtang trek."),
    ("Timure", "villages", "Rasuwa", "Timure", 28.245, 85.380, "Tamang village near the Rasuwagadhi border crossing with Tibet."),
    ("Briddim", "villages", "Rasuwa", "Briddim", 28.135, 85.330, "Ancient Tamang village on the Langtang trail, famous for its traditional slate-roofed houses."),
    ("Thulo Syabru", "villages", "Rasuwa", "Thulo Syabru", 28.078, 85.348, "Tamang village on the Langtang-Gosaikunda route with hot springs nearby."),
    ("Gatlang", "villages", "Rasuwa", "Gatlang", 28.235, 85.230, "Tamang village of Rasuwa with the sacred Parvati Kunda lake above it."),
    ("Parvati Kunda", "lakes", "Rasuwa", "Gatlang", 28.245, 85.245, "Sacred lake above Gatlang village."),
    ("Chandanbari", "villages", "Rasuwa", "Chandanbari", 28.178, 85.510, "Village on the Langtang trail with the famous Chandanbari cheese factory."),
    ("Sing Gompa", "villages", "Rasuwa", "Sing Gompa", 28.108, 85.430, "Buddhist monastery village on the Langtang-Gosaikunda trail."),
]

# existing rows whose district/province should be fixed
FIXES = {
    5139: ("Chitwan", "Bagmati"),  # "Kasara Chitwan" had no district/province
    5793: ("Chitwan", "Bagmati"),  # "Devghat" was in Tanahun; the famous ghats are on the Chitwan bank
}

# names that already exist in ANOTHER district - never create a second entry
SKIP_NAMES = {"Devghat", "Trishuli River"}


def main():
    created = 0
    skipped = 0
    fixed = 0
    for name, cslug, dist, city, lat, lon, short in PLACES:
        if name in SKIP_NAMES:
            skipped += 1
            continue
        aliases = DISTRICT_ALIASES.get(dist, {dist})
        existing = Destination.objects.filter(name__iexact=name).filter(
            district__in=list(aliases) + [None]
        )
        if existing.exists():
            skipped += 1
            for d in existing:
                if not d.province:
                    d.province = "Bagmati"
                    d.save(update_fields=["province"])
                    fixed += 1
            continue
        base = (
            name.lower()
            .replace(" ", "-")
            .replace("(", "")
            .replace(")", "")
            .replace(",", "")
            .replace("'", "")
            .replace("/", "-")
            .replace("&", "and")
            .replace("\u2013", "-")
        )
        slug = base
        if Destination.objects.filter(slug=slug).exists():
            slug = f"{base}-{dist.lower()}"
            if Destination.objects.filter(slug=slug).exists():
                slug = f"{base}-{dist.lower()}-2"
        cat = cats.get(cslug) or cats.get("attraction")
        Destination.objects.create(
            name=name, slug=slug, category=cat, district=dist,
            province="Bagmati", city=city, city_english=city,
            latitude=lat, longitude=lon, short_description=short,
            description=short, country="Nepal", status="approved",
            is_active=True, source="round17-bagmati", views_count=0,
        )
        created += 1

    for did, (dist, prov) in FIXES.items():
        d = Destination.objects.filter(id=did).first()
        if d:
            d.district = dist
            d.province = prov
            d.save(update_fields=["district", "province"])
            fixed += 1

    print(f"created: {created} | skipped (already exist): {skipped} | fixed: {fixed}")


if __name__ == "__main__":
    main()
