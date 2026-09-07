"""Round 19: Add Sudurpashchim Province famous named places (Achham, Baitadi,
Bajhang, Bajura, Dadeldhura, Darchula, Doti) from the ward-by-ward district
data as real destinations. Skips existing, disambiguates slug collisions,
fixes Parshuram Dham's district (was Doti; the canonical site is in
Dadeldhura's Parshuram Municipality).
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

DISTRICT_ALIASES = {
    "Achham": {"Achham", "अछाम", "अछाम जिल्ला", "Achham District"},
    "Baitadi": {"Baitadi", "बैतडी", "बैतडी जिल्ला", "Baitadi District"},
    "Bajhang": {"Bajhang", "बझाङ", "बझाङ जिल्ला", "Bajhang District"},
    "Bajura": {"Bajura", "बाजुरा", "बाजुरा जिल्ला", "Bajura District"},
    "Dadeldhura": {"Dadeldhura", "डडेल्धुरा", "डडेल्धुरा जिल्ला", "Dadeldhura District"},
    "Darchula": {"Darchula", "दार्चुला", "दार्चुला जिल्ला", "Darchula District"},
    "Doti": {"Doti", "डोटी", "डोटी जिल्ला", "Doti District"},
}

# (name, category_slug, district, city, lat, lon, short_description)
PLACES = [
    # ================= ACHHAM =================
    ("Jingale Lake", "lakes", "Achham", "Ramaroshan", 29.370, 81.320, "One of the twelve lakes of the Ramaroshan complex."),
    ("Mangalsen Durbar", "heritage", "Achham", "Mangalsen", 29.170, 81.220, "Historic durbar of Mangalsen, the district headquarters of Achham."),
    ("Bannigadhi", "heritage", "Achham", "Bannigadhi Jayagadh", 29.100, 81.150, "Historic fort (gadhi) of Achham."),
    ("Jayagadh", "heritage", "Achham", "Bannigadhi Jayagadh", 29.120, 81.130, "Historic fort site of Achham."),
    # ================= BAITADI =================
    ("Tripurasundari Bhagawati Temple", "temples", "Baitadi", "Dasharathchand", 29.550, 80.420, "One of Baitadi's four sister-goddess temples."),
    ("Nigalasaini Bhagawati Temple", "temples", "Baitadi", "Dasharathchand", 29.520, 80.450, "Sister-goddess temple of Baitadi."),
    ("Dilasaini Bhagawati Temple", "temples", "Baitadi", "Dilasaini", 29.600, 80.300, "Sister-goddess temple of Dilasaini."),
    ("Rauleshwar Kedar", "temples", "Baitadi", "Surnaya", 29.650, 80.500, "Kedar shrine of Surnaya in the Seven Kedar circuit."),
    ("Deulek Kedar", "temples", "Baitadi", "Dogada Kedar", 29.580, 80.480, "Kedar shrine of Dogada."),
    ("Sigas Kedar", "temples", "Baitadi", "Sigas", 29.620, 80.520, "Kedar shrine of Sigas."),
    # ================= BAJHANG =================
    ("Kedarseu", "temples", "Bajhang", "Kedarseu", 29.700, 81.250, "Kedar religious landscape giving Kedarseu Rural Municipality its name."),
    # ================= BAJURA =================
    ("Gaumul", "mountains", "Bajura", "Gaumul", 29.620, 81.480, "Highland area of Gaumul with alpine pastures and trekking."),
    ("Budhiganga River", "rivers", "Bajura", "Budhiganga", 29.400, 81.400, "River of far-west Nepal flowing through Bajura and Achham."),
    ("Himali (Bajura)", "villages", "Bajura", "Himali", 29.720, 81.550, "Remote high-Himalayan area of Bajura suited to wilderness trekking."),
    # ================= DADELDHURA =================
    ("Ghatalthan", "pilgrimage", "Dadeldhura", "Amargadhi", 29.270, 80.550, "Religious-cultural site of Dadeldhura in the provincial tourism package."),
    ("Asirgram", "villages", "Dadeldhura", "Amargadhi", 29.250, 80.520, "Rural-cultural village of Dadeldhura's Amargadhi circuit."),
    ("Jogbudha", "temples", "Dadeldhura", "Parshuram", 29.170, 80.330, "Temple of Parshuram municipality, Dadeldhura."),
    # ================= DARCHULA =================
    ("Byas (Darchula)", "villages", "Darchula", "Byas", 29.950, 80.650, "High-Himalayan area of Byas near the Api-Nampa region."),
    # ================= DOTI =================
    ("Silgadhi Heritage Area", "heritage", "Doti", "Dipayal Silgadhi", 29.260, 80.930, "Historic landscape of Silgadhi, the district headquarters of Doti."),
]

# existing rows whose district should be fixed
FIXES = {
    7527: ("Dadeldhura", "Sudurpashchim"),  # Parshuram Dham - canonical site is in Dadeldhura
}


def main():
    created = 0
    skipped = 0
    fixed = 0
    for name, cslug, dist, city, lat, lon, short in PLACES:
        aliases = DISTRICT_ALIASES.get(dist, {dist})
        existing = Destination.objects.filter(name__iexact=name).filter(
            district__in=list(aliases) + [None]
        )
        if existing.exists():
            skipped += 1
            for d in existing:
                if not d.province:
                    d.province = "Sudurpashchim"
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
            .replace("\u0101", "a")
        )
        slug = base
        if Destination.objects.filter(slug=slug).exists():
            slug = f"{base}-{dist.lower()}"
            if Destination.objects.filter(slug=slug).exists():
                slug = f"{base}-{dist.lower()}-2"
        cat = cats.get(cslug) or cats.get("attraction")
        Destination.objects.create(
            name=name, slug=slug, category=cat, district=dist,
            province="Sudurpashchim", city=city, city_english=city,
            latitude=lat, longitude=lon, short_description=short,
            description=short, country="Nepal", status="approved",
            is_active=True, source="round19-sudurpashchim", views_count=0,
        )
        created += 1

    for did, (dist, prov) in FIXES.items():
        d = Destination.objects.filter(id=did).first()
        if d:
            d.district = dist
            d.province = prov
            d.save(update_fields=["district", "province"])
            fixed += 1
            print(f"fixed {d.name} -> {dist}")

    print(f"created: {created} | skipped (already exist): {skipped} | fixed: {fixed}")


if __name__ == "__main__":
    main()
