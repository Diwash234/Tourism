"""
Attach the 20 curated local AI Nepal photos (stored in
frontend/Tourism/public/images/destinations/<place>/*.jpg and SERVED
STATICALLY by Vite as /images/destinations/...) to their matching headline
destinations. Also tops-up every destination's gallery to at least N
diverse curated Unsplash photos so cards and the CircularGallery have
rich content.

IMPORTANT: The AI photos are linked via external_url=/images/... STATIC
paths (NOT by saving into ImageField). This is deliberate: the files live
in the React public/ folder (committed to git, served by Vite), so they
work out of the box after `git pull` with no media/ setup and no
broken /media/... 404s.

This command is IDEMPOTENT and SAFE to re-run.

Usage:
    python manage.py attach_local_photos
    python manage.py attach_local_photos --skip-local
    python manage.py attach_local_photos --gallery-target 20
    python manage.py attach_local_photos --limit 100
"""
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from tourist.models import Destination, DestinationImage
from tourist import photo_catalog


# key -> (static path, caption, tags)  -- files are in frontend/Tourism/public/
LOCAL_PHOTOS = {
    "nagarkot":  ("/images/destinations/nagarkot/sunrise-view.jpg",
                  "Nagarkot sunrise over the Himalayas", "mountain,sunrise,viewpoint"),
    "pokhara":   ("/images/destinations/pokhara/fewatal.jpg",
                  "Phewa Lake & Tal Barahi, Pokhara", "lake,city,boating"),
    "everest":   ("/images/destinations/everest/base-camp.jpg",
                  "Everest Base Camp, Khumbu", "mountain,trek,khumbu"),
    "kathmandu": ("/images/destinations/kathmandu/durbar-square.jpg",
                  "Kathmandu Valley heritage", "heritage,temple,stupa"),
    "chitwan":   ("/images/destinations/chitwan/safari.jpg",
                  "Chitwan National Park jungle safari", "wildlife,safari,jungle"),
    "lumbini":   ("/images/destinations/lumbini/garden.jpg",
                  "Lumbini, birthplace of the Buddha", "heritage,religious,pilgrimage"),
    "bhaktapur": ("/images/destinations/bhaktapur/durbar.jpg",
                  "Bhaktapur Durbar Square", "heritage,newari,temple"),
    "annapurna": ("/images/destinations/annapurna/trek.jpg",
                  "Annapurna Base Camp trek", "mountain,trek,circuit"),
    "patan":     ("/images/destinations/patan/durbar.jpg",
                  "Patan Durbar Square, Lalitpur", "heritage,newari,temple"),
    "mustang":   ("/images/destinations/mustang/lo-manthang.jpg",
                  "Lo Manthang, Upper Mustang", "mountain,tibetan,highland"),
    "ilam":      ("/images/destinations/ilam/tea-gardens.jpg",
                  "Ilam tea gardens & Kanyam", "hill,tea,greenery"),
    "janakpur":  ("/images/destinations/janakpur/janaki-mandir.jpg",
                  "Janaki Mandir, Janakpurdham", "heritage,temple,hindu"),
    "bandipur":  ("/images/destinations/bandipur/hilltop-village.jpg",
                  "Bandipur heritage hilltop village", "hill,village,newari"),
    "bardiya":   ("/images/destinations/bardiya/tiger-reserve.jpg",
                  "Bardiya (Bardia) National Park", "wildlife,jungle,tiger"),
    "dolpo":     ("/images/destinations/dolpo/highland-village.jpg",
                  "Dolpo Saldang highland village", "mountain,tibetan,remote"),
    "gosaikunda":("/images/destinations/gosaikunda/glacial-lake.jpg",
                  "Gosaikunda holy glacial lake", "lake,pilgrimage,alpine"),
    "koshi-tappu":("/images/destinations/koshi-tappu/wetlands.jpg",
                  "Koshi Tappu Wildlife Reserve wetlands", "wildlife,birds,wetlands"),
    "manaslu":   ("/images/destinations/manaslu/mountain-peak.jpg",
                  "Mount Manaslu viewpoint panorama", "mountain,peak,trek"),
    "rara":      ("/images/destinations/rara/alpine-lake.jpg",
                  "Rara Lake & National Park", "lake,nationalpark,alpine"),
    "tilicho":   ("/images/destinations/tilicho/himalayan-lake.jpg",
                  "Tilicho Lake high-altitude Himalayan lake", "lake,mountain,alpine"),
}


def _pool_for(dest):
    name = (dest.name or "").lower()
    cat = (getattr(dest.category, "name", "") or "").lower()
    hay = f"{name} {cat}"
    if any(k in hay for k in ("lake", "tal", "pokhari", "kunda", "sarovar")): return "LAKE"
    if any(k in hay for k in ("waterfall", "jharna", "fall")): return "WATERFALL"
    if any(k in hay for k in ("temple", "mandir", "stupa", "durbar", "gompa",
                              "monastery", "heritage", "church", "mosque",
                              "religious", "pashupati", "boudha", "swayambhu",
                              "lumbini", "janakpur")): return "HERITAGE"
    if any(k in hay for k in ("national park", "safari", "wildlife", "reserve",
                              "chitwan", "bardiya", "koshi", "tappu")): return "WILDLIFE"
    if any(k in hay for k in ("hotel", "lodge", "resort", "guest house", "homestay",
                              "backpackers", "hostel", "cottages")): return "HOTEL"
    if any(k in hay for k in ("himal", "peak", "mount", "everest", "annapurna",
                              "manaslu", "dhaulagiri", "langtang", "makalu",
                              "kanchenjunga", "trek", "himalaya", "base camp",
                              "pass", "la", "danda", "hill", "viewpoint",
                              "nagarkot", "sarankot", "dhulikhel")): return "MOUNTAIN"
    if any(k in hay for k in ("chowk", "bazaar", "market", "city",
                              "kathmandu", "thamel")): return "CITY"
    return "GENERAL"


def _get_pool(name):
    attr = name + "_PHOTOS"
    pool = getattr(photo_catalog, attr, None) or []
    if not pool:
        return []
    return pool


def _pick(pool, seed):
    if not pool:
        fallback = [
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1400&q=80",
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1400&q=80",
            "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400&q=80",
        ]
        return {"url": fallback[seed % len(fallback)], "author": "Unsplash",
                "license": "Unsplash License", "source_url": "https://unsplash.com/"}
    h = (seed * 2654435761) & 0xFFFFFFFF
    return pool[h % len(pool)]


class Command(BaseCommand):
    help = "Attach 20 local AI Nepal photos (static /images/ paths) to headline destinations + top-up galleries."

    def add_arguments(self, parser):
        parser.add_argument("--skip-local", action="store_true",
                            help="Skip attaching the 20 local AI photos; only top-up galleries.")
        parser.add_argument("--gallery-target", type=int, default=13,
                            help="Target gallery size per destination (default 13).")
        parser.add_argument("--limit", type=int, default=0,
                            help="Only process N destinations (for test runs).")

    def handle(self, *args, **options):
        skip_local = options["skip_local"]
        target = options["gallery_target"]
        limit = options["limit"]
        attached_local = 0

        if not skip_local:
            for key, (static_url, caption, tags) in LOCAL_PHOTOS.items():
                # Find a non-hotel destination whose name contains the key
                qs = Destination.objects.filter(name__icontains=key.replace("-", " ")).order_by("name")
                dest = None
                for cand in qs:
                    n = cand.name.lower()
                    if any(w in n for w in ("hotel", "resort", "lodge", "guest house",
                                            "restaurant", "cafe", "dhawa", "homestay",
                                            "backpackers", "hostel", "motel", "cottages",
                                            "food home", "bakery")):
                        continue
                    dest = cand
                    break
                if dest is None:
                    dest = qs.first()
                if not dest:
                    self.stderr.write(self.style.WARNING(f"  !! {key}: no match, skipping"))
                    continue

                # Idempotent: if we already have a REFERENCE row pointing at
                # this static_url for this destination, skip.
                if dest.gallery.filter(external_url=static_url).exists():
                    self.stdout.write(f"  -- {key}: already attached to '{dest.name}'")
                    continue

                # Clear other is_cover flags
                dest.gallery.update(is_cover=False)
                # Clear stale cover_image field if it holds an old URL
                if dest.cover_image:
                    dest.cover_image = ""
                    dest.save(update_fields=["cover_image"])
                DestinationImage.objects.create(
                    destination=dest,
                    external_url=static_url,
                    thumbnail_url=static_url.replace("w=1400", "w=500").replace("/images/destinations/", "/images/destinations/"),
                    caption=caption,
                    source=DestinationImage.Source.REFERENCE,
                    photographer="Nepal Tourism Platform (AI)",
                    license_type="Platform-generated (royalty-free)",
                    source_url=f"static://{static_url}",
                    image_category="attraction",
                    is_cover=True,
                    verification_status=DestinationImage.ImageStatus.APPROVED,
                    is_verified=True,
                    authenticity_score=0.9,
                    attribution="AI-generated for Nepal Tourism",
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  OK {key:12s} -> #{dest.id} {dest.name[:50]}"))
                attached_local += 1

        # ---- 2. Top-up galleries with curated Unsplash URLs ----
        added = 0
        qs = Destination.objects.all().order_by("id")
        if limit:
            qs = qs[:limit]
        total = qs.count() if hasattr(qs, "count") else len(qs)
        for i, dest in enumerate(qs, 1):
            existing = dest.gallery.count()
            if existing >= target:
                continue
            pool_name = _pool_for(dest)
            pool = list(_get_pool(pool_name))
            # Merge with general pool for variety if small
            general = list(_get_pool("GENERAL"))
            if len(pool) < (target - existing):
                pool = pool + general
            if not pool:
                continue
            seen = set(dest.gallery.exclude(external_url__isnull=True)
                        .exclude(external_url="").values_list("external_url", flat=True))
            need_cover = not dest.gallery.filter(is_cover=True).exists()
            with transaction.atomic():
                attempts = 0
                added_this = 0
                while added_this < (target - existing) and attempts < 200:
                    p = _pick(pool, dest.id * 131 + attempts)
                    url = p.get("url") if isinstance(p, dict) else p
                    if url and url not in seen:
                        DestinationImage.objects.create(
                            destination=dest,
                            external_url=url,
                            thumbnail_url=url.replace("w=1400", "w=500"),
                            caption=p.get("author", "Nepal travel photo") if isinstance(p, dict) else "Nepal travel photo",
                            source=DestinationImage.Source.UNSPLASH,
                            photographer=p.get("author", "Unsplash") if isinstance(p, dict) else "Unsplash",
                            license_type=p.get("license", "Unsplash License") if isinstance(p, dict) else "Unsplash License",
                            source_url=p.get("source_url", "https://unsplash.com/") if isinstance(p, dict) else "https://unsplash.com/",
                            image_category=pool_name.lower(),
                            is_cover=need_cover and added_this == 0,
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            authenticity_score=0.6,
                            attribution=p.get("author", "Unsplash") if isinstance(p, dict) else "Unsplash",
                        )
                        seen.add(url)
                        added_this += 1
                    attempts += 1
                added += added_this
            if i % 500 == 0:
                self.stdout.write(f"  ...processed {i}/{total}, added {added} images so far")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Attached {attached_local} local AI photos, added {added} "
            f"curated gallery images. Final counts: "
            f"{Destination.objects.count()} destinations / "
            f"{DestinationImage.objects.count()} images."
        ))
