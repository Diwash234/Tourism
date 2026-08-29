"""
Import & enrich every Nepal place from the cleaned OpenStreetMap dataset
(ml_service/processed_data/destinations_clean.csv, 12,800+ places) into the
Destination table, and enrich ALL existing records with generated
descriptions, correct categories, and cities/districts.

What it does
------------
1. Reads the clean CSV (ID, Name, Type, Tourism_Category, lat/lon, City,
   Area, District, Province).
2. For every CSV row not yet in the DB (matched by external_id), creates a
   new approved Destination.
3. For every destination missing a description, generates an honest,
   place-specific description from its name, type, district and province --
   no fabricated reviews or ratings.
4. Ensures every destination has a category, city, district and province.
5. Optionally assigns accurate photos via the photo catalog.

This is intentionally OFFLINE -- it does not call Wikipedia or any paid API
-- so it can run in any environment. It uses the real OSM dataset shipped in
the repo (originally extracted via the Overpass API, which is free and open).

Usage:
    python manage.py import_osm_destinations
    python manage.py import_osm_destinations --photos
    python manage.py import_osm_destinations --limit 500 --photos
"""
import csv
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from tourist.models import Destination, Category


# CSV file (relative to Tourism/ app dir)
CSV_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                 "ml_service", "processed_data", "destinations_clean.csv")
)

# OSM tourism_category -> Category (by name). Falls back to the matching
# OSM category row, then to "attraction" if all else fails.
OSM_CATEGORY_MAP = {
    "hotel": "hotel",
    "guest_house": "guest_house",
    "hostel": "hostel",
    "motel": "motel",
    "apartment": "apartment",
    "resort": "resort",
    "camp_site": "camp_site",
    "camp_pitch": "camp_site",
    "alpine_hut": "alpine_hut",
    "wilderness_hut": "wilderness_hut",
    "chalet": "chalet",
    "viewpoint": "viewpoint",
    "attraction": "attraction",
    "museum": "museum",
    "gallery": "gallery",
    "artwork": "artwork",
    "information": "information",
    "theme_park": "theme_park",
    "picnic_site": "picnic_site",
    "zoo": "zoo",
    "aquarium": "aquarium",
    "trailhead": "Nature & Trekking",
    "route": "Nature & Trekking",
    "travel_agency": "information",
}


def generate_description(name, category_name, district, province, city):
    """Build an honest, informative description from real fields."""
    place = name.strip()
    where = city or district or province
    parts = []
    cat = (category_name or "").lower()

    if "temple" in place.lower() or "mandir" in place.lower() or "stupa" in place.lower() or "gompa" in place.lower() or "church" in place.lower() or "mosque" in place.lower():
        parts.append(f"{place} is a religious site")
    elif "viewpoint" in cat or "view point" in place.lower() or "viewtower" in place.lower():
        parts.append(f"{place} is a scenic viewpoint")
    elif "museum" in cat:
        parts.append(f"{place} is a museum")
    elif "hotel" in cat or "resort" in cat:
        parts.append(f"{place} is a hotel/lodge")
    elif "guest" in cat or "hostel" in cat or "homestay" in cat:
        parts.append(f"{place} is a traveller accommodation")
    elif "camp" in cat or "hut" in cat or "chalet" in cat:
        parts.append(f"{place} is an outdoor stay/camping site")
    elif "park" in cat or "wildlife" in cat or "safari" in cat:
        parts.append(f"{place} is a nature and wildlife area")
    elif "trek" in cat or "trail" in cat or "mountain" in cat or "peak" in cat:
        parts.append(f"{place} is a trekking and mountain destination")
    elif "lake" in place.lower() or "pokhari" in place.lower() or "tal" in place.lower().split():
        parts.append(f"{place} is a lake/water body")
    elif "fall" in place.lower() or "jharana" in place.lower():
        parts.append(f"{place} is a waterfall")
    else:
        parts.append(f"{place} is a tourism destination")

    if where:
        parts.append(f"located in {where}")
    if province and province != where:
        parts.append(f"in {province}, Nepal")
    elif not where:
        parts.append("in Nepal")

    desc = ", ".join(parts) + "."
    # Add practical, honest context by type
    if any(w in cat for w in ("hotel", "resort", "guest", "hostel", "lodge", "homestay", "camp", "hut", "chalet", "apartment", "motel")):
        desc += " It offers accommodation for travellers exploring the surrounding area; check current availability and pricing directly."
    elif "viewpoint" in cat:
        desc += " It offers panoramic views of the surrounding landscape and is best visited in clear weather, especially at sunrise or sunset."
    elif "museum" in cat or "gallery" in cat:
        desc += " It showcases local history, art and culture; visiting hours and entry fees may vary by season."
    elif "religious" in desc.lower() or any(w in place.lower() for w in ("temple", "mandir", "stupa", "gompa")):
        desc += " Visitors are asked to dress respectfully and follow local customs and photography rules."
    else:
        desc += " It is part of Nepal's network of mapped tourism places contributed by OpenStreetMap."

    return desc


class Command(BaseCommand):
    help = "Import all places from destinations_clean.csv and enrich descriptions/categories."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Only process N CSV rows (for testing).")
        parser.add_argument("--photos", action="store_true", help="Also (re)assign cover photos after import.")
        parser.add_argument("--enrich-only", action="store_true", help="Skip importing; only enrich existing descriptions.")

    def handle(self, *args, **options):
        cat_cache = {c.name.lower(): c for c in Category.objects.all()}

        def get_category(osm_cat):
            key = (OSM_CATEGORY_MAP.get((osm_cat or "").strip().lower()) or osm_cat or "attraction").strip().lower()
            if key in cat_cache:
                return cat_cache[key]
            # try case-insensitive contains
            for k, v in cat_cache.items():
                if key and (key in k or k in key):
                    return v
            return cat_cache.get("attraction")

        if not os.path.exists(CSV_PATH):
            self.stderr.write(self.style.ERROR(f"CSV not found: {CSV_PATH}"))
            return

        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if options["limit"]:
            rows = rows[: options["limit"]]

        self.stdout.write(f"Loaded {len(rows)} CSV rows from {os.path.basename(CSV_PATH)}")

        created = 0
        enriched = 0
        unchanged = 0

        for i, row in enumerate(rows, 1):
            try:
                ext_id = int(row["ID"]) if row.get("ID", "").isdigit() else None
                name = (row.get("Name") or "").strip()
                if not name or ext_id is None:
                    continue

                cat = get_category(row.get("Tourism_Category"))
                city = (row.get("City") or "").strip()
                district = (row.get("District") or "").strip()
                province = (row.get("Province") or "").strip()
                lat = row.get("Latitude")
                lon = row.get("Longitude")

                dest = Destination.objects.filter(external_id=ext_id).first()
                if dest is None and not options["enrich_only"]:
                    # Create with a unique slug
                    base = slugify(name) or f"place-{ext_id}"
                    slug = base
                    n = 2
                    while Destination.objects.filter(slug=slug).exists():
                        slug = f"{base}-{n}"
                        n += 1
                    dest = Destination.objects.create(
                        external_id=ext_id,
                        name=name[:200],
                        slug=slug[:220],
                        type=(row.get("Type") or "")[:100],
                        category=cat,
                        city=city,
                        city_nepali=(row.get("Area") or "")[:200],
                        district=district,
                        province=province,
                        latitude=lat or None,
                        longitude=lon or None,
                        country="Nepal",
                        status="approved",
                        is_active=True,
                    )
                    created += 1
                elif dest is None:
                    continue

                # Enrich missing fields
                update = []
                if not dest.category_id and cat:
                    dest.category = cat
                    update.append("category")
                if not dest.city and city:
                    dest.city = city
                    update.append("city")
                if not dest.district and district:
                    dest.district = district
                    update.append("district")
                if not dest.province and province:
                    dest.province = province
                    update.append("province")
                if not dest.latitude and lat:
                    dest.latitude = lat
                    update.append("latitude")
                if not dest.longitude and lon:
                    dest.longitude = lon
                    update.append("longitude")
                if not dest.country:
                    dest.country = "Nepal"
                    update.append("country")

                if not dest.description:
                    cat_name = dest.category.name if dest.category_id else (row.get("Tourism_Category") or "")
                    dest.description = generate_description(
                        dest.name, cat_name, dest.district, dest.province, dest.city
                    )
                    dest.short_description = dest.description[:280]
                    update.extend(["description", "short_description"])

                if dest.status != "approved":
                    dest.status = "approved"
                    update.append("status")
                if not dest.is_active:
                    dest.is_active = True
                    update.append("is_active")

                if update:
                    dest.save(update_fields=list(set(update)))
                    enriched += 1
                else:
                    unchanged += 1

                if i % 1000 == 0:
                    self.stdout.write(f"  [{i}/{len(rows)}] created={created} enriched={enriched}")

            except Exception as exc:
                self.stderr.write(f"  row {i} ({row.get('Name','?')}): {type(exc).__name__}: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. created={created} enriched={enriched} unchanged={unchanged} total_destinations={Destination.objects.count()}"
        ))

        if options["photos"]:
            from django.core.management import call_command
            self.stdout.write("Assigning photos...")
            call_command("assign_destination_photos")
