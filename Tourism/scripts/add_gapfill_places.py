"""Round 20: Final gap-fill for Bagmati/Karnali/Sudurpashchim - the few
remaining named places from the ward-by-ward data (Surkhet Valley, Mahabouddha
Temple, Kamalbazar, Patan Baitadi, Chamere Gufas of Bheriganga/Gurbhakot,
Dullu Malika, Pathangini, Mathurapati Shiva Shrine) as real destinations.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

DISTRICT_ALIASES = {
    "Surkhet": {"Surkhet", "सुर्खेत", "सुर्खेत जिल्ला"},
    "Dailekh": {"Dailekh", "दैलेख", "दैलेख जिल्ला"},
    "Lalitpur": {"Lalitpur", "ललितपुर", "ललितपुर जिल्ला"},
    "Kavrepalanchok": {"Kavrepalanchok", "Kavre", "काभ्रेपलाञ्चोक", "काभ्रेपलाञ्चोक जिल्ला"},
    "Achham": {"Achham", "अछाम", "अछाम जिल्ला"},
    "Baitadi": {"Baitadi", "बैतडी", "बैतडी जिल्ला"},
}

PROVINCE_BY_DISTRICT = {
    "Surkhet": "Karnali", "Dailekh": "Karnali",
    "Lalitpur": "Bagmati", "Kavrepalanchok": "Bagmati",
    "Achham": "Sudurpashchim", "Baitadi": "Sudurpashchim",
}

# (name, category_slug, district, city, lat, lon, short_description)
PLACES = [
    ("Surkhet Valley", "valleys", "Surkhet", "Birendranagar", 28.600, 81.630, "Valley landscape of the Karnali gateway city of Birendranagar."),
    ("Chamere Gufa Bheriganga", "caves", "Surkhet", "Bheriganga", 28.490, 81.460, "Bat cave of Bheriganga Ward 4."),
    ("Chamere Gufa Gurbhakot", "caves", "Surkhet", "Gurbhakot", 28.460, 81.540, "Bat cave of Gurbhakot Ward 7."),
    ("Dullu Malika", "temples", "Dailekh", "Dullu", 28.860, 81.690, "Goddess site of Dullu Ward 13 in the Panchakoshi tourism area."),
    ("Pathangini", "pilgrimage", "Dailekh", "Dullu", 28.855, 81.695, "Panchakoshi-area site of Dullu Ward 7 with tourism infrastructure."),
    ("Mahabouddha Temple", "buddhist-sites", "Lalitpur", "Lalitpur", 27.670, 85.317, "Terracotta Buddhist temple of Patan known as the 'Temple of a Thousand Buddhas'."),
    ("Mathurapati Shiva Shrine", "temples", "Kavrepalanchok", "Namobuddha", 27.600, 85.580, "Shiva shrine of Mathurapati, a pilgrimage site of Namobuddha municipality."),
    ("Kamalbazar", "cities", "Achham", "Kamalbazar", 29.050, 81.300, "Market town of Achham district."),
    ("Patan Baitadi", "cities", "Baitadi", "Patan", 29.440, 80.530, "Historic market town and municipality of Baitadi district."),
]


def main():
    created = 0
    skipped = 0
    for name, cslug, dist, city, lat, lon, short in PLACES:
        aliases = DISTRICT_ALIASES.get(dist, {dist})
        existing = Destination.objects.filter(name__iexact=name).filter(
            district__in=list(aliases) + [None]
        )
        if existing.exists():
            skipped += 1
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
            province=PROVINCE_BY_DISTRICT[dist], city=city, city_english=city,
            latitude=lat, longitude=lon, short_description=short,
            description=short, country="Nepal", status="approved",
            is_active=True, source="round20-gapfill", views_count=0,
        )
        created += 1
    print(f"created: {created} | skipped: {skipped}")


if __name__ == "__main__":
    main()
