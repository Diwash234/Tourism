"""
Reassign cover photos for ALL destinations using photo_catalog.resolve_cover_photo.
Then ensure every destination has a gallery of curated images.
Idempotent and safe to re-run.

Usage:
    python manage.py reassign_covers
    python manage.py reassign_covers --gallery-target 13
    python manage.py reassign_covers --limit 200
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination, DestinationImage
from tourist import photo_catalog


# Static AI photos for 20 headline places (same map used in photo_catalog.LANDMARK_PHOTOS).
# These keys match SUBSTRINGS of destination names (non-accommodation only).
STATIC_AI_KEYS = [
    ("nagarkot",            "/images/destinations/nagarkot/sunrise-view.jpg",      "Nagarkot sunrise over the Himalayas"),
    ("phewa",               "/images/destinations/pokhara/fewatal.jpg",            "Phewa Lake & Tal Barahi, Pokhara"),
    ("fewa tal",            "/images/destinations/pokhara/fewatal.jpg",            "Phewa Lake & Tal Barahi, Pokhara"),
    ("fewa",                "/images/destinations/pokhara/fewatal.jpg",            "Phewa Lake & Tal Barahi, Pokhara"),
    ("everest base camp",   "/images/destinations/everest/base-camp.jpg",          "Everest Base Camp, Khumbu"),
    ("ebc",                 "/images/destinations/everest/base-camp.jpg",          "Everest Base Camp, Khumbu"),
    ("mount everest",       "/images/destinations/everest/base-camp.jpg",          "Mount Everest (Sagarmatha)"),
    ("sagarmatha",          "/images/destinations/everest/base-camp.jpg",          "Sagarmatha (Everest)"),
    ("kathmandu durbar",    "/images/destinations/kathmandu/durbar-square.jpg",    "Kathmandu Durbar Square"),
    ("chitwan",             "/images/destinations/chitwan/safari.jpg",             "Chitwan National Park jungle safari"),
    ("lumbini",             "/images/destinations/lumbini/garden.jpg",             "Lumbini, birthplace of the Buddha"),
    ("bhaktapur durbar",    "/images/destinations/bhaktapur/durbar.jpg",           "Bhaktapur Durbar Square"),
    ("bhaktapur",           "/images/destinations/bhaktapur/durbar.jpg",           "Bhaktapur Durbar Square"),
    ("annapurna base camp", "/images/destinations/annapurna/trek.jpg",             "Annapurna Base Camp trek"),
    ("annapurna circuit",   "/images/destinations/annapurna/trek.jpg",             "Annapurna Circuit trek"),
    ("annapurna",           "/images/destinations/annapurna/trek.jpg",             "Annapurna region trek"),
    ("patan durbar",        "/images/destinations/patan/durbar.jpg",               "Patan Durbar Square, Lalitpur"),
    ("patan",               "/images/destinations/patan/durbar.jpg",               "Patan Durbar Square, Lalitpur"),
    ("lalitpur",            "/images/destinations/patan/durbar.jpg",               "Patan Durbar Square, Lalitpur"),
    ("mustang",             "/images/destinations/mustang/lo-manthang.jpg",        "Lo Manthang, Upper Mustang"),
    ("ilam",                "/images/destinations/ilam/tea-gardens.jpg",           "Ilam tea gardens & Kanyam"),
    ("kanyam",              "/images/destinations/ilam/tea-gardens.jpg",           "Kanyam tea gardens, Ilam"),
    ("janakpur",            "/images/destinations/janakpur/janaki-mandir.jpg",     "Janaki Mandir, Janakpurdham"),
    ("janaki mandir",       "/images/destinations/janakpur/janaki-mandir.jpg",     "Janaki Mandir, Janakpurdham"),
    ("bandipur",            "/images/destinations/bandipur/hilltop-village.jpg",   "Bandipur heritage hilltop village"),
    ("bardiya",             "/images/destinations/bardiya/tiger-reserve.jpg",      "Bardiya National Park"),
    ("dolpo",               "/images/destinations/dolpo/highland-village.jpg",     "Dolpo highland village"),
    ("gosaikunda",          "/images/destinations/gosaikunda/glacial-lake.jpg",    "Gosaikunda glacial lake"),
    ("gosainkunda",         "/images/destinations/gosaikunda/glacial-lake.jpg",    "Gosaikunda glacial lake"),
    ("koshi tappu",         "/images/destinations/koshi-tappu/wetlands.jpg",       "Koshi Tappu Wildlife Reserve"),
    ("manaslu",             "/images/destinations/manaslu/mountain-peak.jpg",      "Mount Manaslu"),
    ("rara",                "/images/destinations/rara/alpine-lake.jpg",           "Rara Lake"),
    ("tilicho",             "/images/destinations/tilicho/himalayan-lake.jpg",     "Tilicho Lake"),
]

ACCOMMODATION_HINTS = (
    "hotel", "resort", "lodge", "guest house", "guesthouse", "guest_house",
    "homestay", "home stay", "backpackers", "hostel", "motel", "cottages",
    "restaurant", "cafe", "dhaba", "bakery", "food home", "tea house",
    "teahouse", "inn", "alpine hut", "camp site", "camp_pitch", "chalet",
    "apartment", "villa",
)


def _is_accommodation(dest) -> bool:
    cat = (getattr(dest.category, "slug", "") or "").lower()
    if photo_catalog.is_accommodation_category(cat):
        return True
    name = (dest.name or "").lower()
    for w in ACCOMMODATION_HINTS:
        if w in name:
            return True
    return False


def _find_static_match(dest) -> str | None:
    """Return a static /images/destinations/... URL for this destination.

    Only matches on the destination NAME (strongest signal). We deliberately
    do NOT match on city/district because e.g. a place called "Mahendra Cave"
    with city="Pokhara" should NOT get the Phewa Lake/Pokhara photo.
    """
    if _is_accommodation(dest):
        return None
    name_hay = (dest.name or "").lower()
    # Sort longest-first so "everest base camp" beats "everest", "janaki mandir" beats "janakpur", etc.
    for key, url, _cap in sorted(STATIC_AI_KEYS, key=lambda x: -len(x[0])):
        if key in name_hay:
            return url
    return None


def _build_gallery_pool(dest) -> list:
    """Return a list of photo dicts appropriate for the destination."""
    resolved = photo_catalog.resolve_cover_photo(dest)
    # Determine the primary pool from resolver via CATEGORY_POOLS category matching
    cat_name = getattr(getattr(dest, "category", None), "name", "") or ""
    pool = photo_catalog._category_pool(cat_name)
    if pool is None:
        name = dest.name or ""
        hay = photo_catalog._norm(f"{name} {dest.city or ''} {dest.district or ''}")
        for key in sorted(photo_catalog.CATEGORY_POOLS.keys(), key=len, reverse=True):
            if photo_catalog._norm(key) in hay:
                pool = photo_catalog.CATEGORY_POOLS[key]
                break
    if pool is None:
        if _is_accommodation(dest):
            pool = photo_catalog.HOTEL_PHOTOS
        else:
            pool = photo_catalog.GENERAL_PHOTOS

    # Mix in general pool for variety
    combined = []
    seen_urls = set()
    for source in (pool, photo_catalog.ATTRACTION_PHOTOS, photo_catalog.GENERAL_PHOTOS,
                   photo_catalog.HERITAGE_PHOTOS, photo_catalog.MOUNTAIN_PHOTOS):
        for p in source:
            u = p.get("url")
            if u and u not in seen_urls:
                combined.append(p)
                seen_urls.add(u)
    # Make sure the resolved cover is first
    cover_url = resolved.get("url")
    if cover_url and cover_url not in seen_urls:
        combined.insert(0, resolved)
    return combined


class Command(BaseCommand):
    help = "Reassign covers + populate galleries for all destinations using photo_catalog."

    def add_arguments(self, parser):
        parser.add_argument("--gallery-target", type=int, default=12,
                            help="Gallery size target per destination (default 12).")
        parser.add_argument("--limit", type=int, default=0,
                            help="Process only N destinations (test run).")
        parser.add_argument("--only-missing", action="store_true",
                            help="Only touch destinations that have no cover.")

    def handle(self, *args, **options):
        target = options["gallery_target"]
        limit = options["limit"]
        only_missing = options["only_missing"]

        qs = Destination.objects.all().order_by("id")
        if limit:
            qs = qs[:limit]

        updated_covers = 0
        added_images = 0
        processed = 0
        total = Destination.objects.count() if not limit else limit

        for dest in qs:
            processed += 1
            existing_urls = set(
                dest.gallery.exclude(external_url__isnull=True)
                .exclude(external_url="").values_list("external_url", flat=True)
            )
            has_cover = dest.gallery.filter(is_cover=True).exists()

            if only_missing and has_cover and len(existing_urls) >= target:
                continue

            # 1. Decide cover URL: prefer static AI if keyword matches, else resolver
            static_url = _find_static_match(dest)
            if static_url:
                cover_url = static_url
                cover_caption = next((c for k, u, c in STATIC_AI_KEYS if u == static_url), dest.name)
                cover_source = DestinationImage.Source.REFERENCE
                cover_photo = "Nepal Tourism Platform (AI)"
                cover_license = "Platform-generated (royalty-free)"
                cover_score = 0.9
            else:
                resolved = photo_catalog.resolve_cover_photo(dest)
                cover_url = resolved.get("url")
                cover_caption = resolved.get("caption") or dest.name
                cover_source = (DestinationImage.Source.REFERENCE
                                if cover_url.startswith("/images/")
                                else DestinationImage.Source.UNSPLASH)
                cover_photo = resolved.get("author", "Unsplash")
                cover_license = resolved.get("license", "Unsplash License")
                cover_score = 0.9 if cover_url.startswith("/images/") else 0.6

            # 2. Set cover (clear old is_cover flags; create or update row)
            if not has_cover or not dest.gallery.filter(is_cover=True, external_url=cover_url).exists():
                with transaction.atomic():
                    # Clear stale ImageField
                    if dest.cover_image:
                        dest.cover_image = ""
                        dest.save(update_fields=["cover_image"])
                    # Demote other covers
                    dest.gallery.filter(is_cover=True).update(is_cover=False)
                    # Get or create cover row
                    if cover_url in existing_urls:
                        dest.gallery.filter(external_url=cover_url).update(is_cover=True)
                    else:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=cover_url,
                            thumbnail_url=cover_url,
                            caption=cover_caption,
                            source=cover_source,
                            photographer=cover_photo,
                            license_type=cover_license,
                            source_url=f"static://{cover_url}" if cover_url.startswith("/") else cover_url,
                            image_category=("attraction" if not _is_accommodation(dest) else "hotel"),
                            is_cover=True,
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            authenticity_score=cover_score,
                            attribution=cover_photo,
                        )
                        existing_urls.add(cover_url)
                        added_images += 1
                    updated_covers += 1

            # 3. Top-up gallery to target size
            if len(existing_urls) < target:
                pool = _build_gallery_pool(dest)
                added_this = 0
                attempts = 0
                while len(existing_urls) < target and added_this < (target - len(existing_urls) + 8) and attempts < 300:
                    p = pool[(dest.id * 131 + attempts) % len(pool)]
                    url = p.get("url")
                    if url and url not in existing_urls:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=url,
                            thumbnail_url=url.replace("w=1400", "w=500") if "unsplash" in url else url,
                            caption=p.get("caption", p.get("author", "Nepal travel photo")),
                            source=(DestinationImage.Source.REFERENCE if url.startswith("/images/")
                                    else DestinationImage.Source.UNSPLASH),
                            photographer=p.get("author", "Unsplash"),
                            license_type=p.get("license", "Unsplash License"),
                            source_url=f"static://{url}" if url.startswith("/") else p.get("source_url", "https://unsplash.com/"),
                            image_category=("attraction" if not _is_accommodation(dest) else "hotel"),
                            is_cover=False,
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            authenticity_score=0.6 if url.startswith("http") else 0.9,
                            attribution=p.get("author", "Unsplash"),
                        )
                        existing_urls.add(url)
                        added_this += 1
                        added_images += 1
                    attempts += 1

            if processed % 500 == 0:
                self.stdout.write(f"  ...{processed}/{total}  covers updated={updated_covers}, images added={added_images}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Processed {processed} destinations, updated {updated_covers} covers, "
            f"added {added_images} gallery images. "
            f"Total images in DB: {DestinationImage.objects.count()}."
        ))
