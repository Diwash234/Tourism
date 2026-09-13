"""
Search the free web (Wikimedia Commons, DuckDuckGo, Openverse) for REAL
photos of each Nepal destination and save them into the database.

No paid / billed API is required. This is what makes the system work
without a ChatGPT/OpenAI subscription.

For every destination it builds a specific query (name + district),
searches all sources, scores each hit against the destination name/region
so e.g. Mustang never gets a Janakpur photo, and stores the best N matches
as DestinationImage rows (cover + gallery) with full source/license metadata.

Usage:
    # One destination (by id or slug)
    python manage.py fetch_destination_images --destination rolpa --num 12

    # A list of off-the-beaten-path districts the user mentioned
    python manage.py fetch_destination_images --district Rolpa,Bajhang,Banke,Achhura

    # The curated major-destination seed list
    python manage.py fetch_destination_images --seed --num 12

    # Every destination in the DB
    python manage.py fetch_destination_images --all --num 10

    # Force-refresh even if a destination already has enough images
    python manage.py fetch_destination_images --seed --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from tourist.models import Destination, DestinationImage
from tourist.services.image_search.search import search_destination_images


SEED_DESTINATIONS = [
    "Pashupatinath", "Boudhanath", "Swayambhunath", "Kathmandu Durbar Square",
    "Patan Durbar Square", "Bhaktapur Durbar Square", "Phewa Lake", "Sarangkot",
    "Davis Falls", "World Peace Pagoda", "Begnas Lake", "Annapurna Base Camp",
    "Everest Base Camp", "Annapurna Circuit", "Poon Hill", "Langtang", "Manaslu",
    "Mustang", "Muktinath", "Chitwan National Park", "Lumbini", "Janakpur",
    "Nagarkot", "Bandipur", "Ghandruk", "Dhampus", "Rara Lake", "Tilicho Lake",
    "Gosaikunda", "Mardi Himal", "Manang", "Namche Bazaar", "Tengboche", "Lukla",
    "Sagarmatha National Park", "Changu Narayan", "Nyatapola", "Kirtipur", "Ilam",
    "Khaptad", "Shey Phoksundo", "Bardiya National Park", "Koshi Tappu",
    "Rolpa", "Bajhang", "Banke", "Achham", "Bahunthan", "Waling", "Syangja",
    "Pokhara", "Dolpa", "Jumla", "Kalikot", "Dailekh", "Jajarkot", "Rukum",
    "Dang", "Surkhet", "Dhangadhi", "Baitadi", "Darchula",
]


class Command(BaseCommand):
    help = "Search free image sources and save real destination photos into the DB."

    def add_arguments(self, parser):
        parser.add_argument("--destination", help="id, slug or name of one destination")
        parser.add_argument("--district", help="comma-separated district names")
        parser.add_argument("--num", type=int, default=12, help="images per destination")
        parser.add_argument("--seed", action="store_true")
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--force", action="store_true",
                            help="re-fetch even if the destination already has enough images")
        parser.add_argument("--min-score", type=float, default=0.30)

    def handle(self, *args, **options):
        targets = self._collect_targets(options)
        if not targets:
            self.stderr.write("No destinations matched. Use --destination, --district, --seed or --all.")
            return

        openverse_key = getattr(settings, "OPENVERSE_API_KEY", "") or ""
        total_saved = 0

        for i, dest in enumerate(targets, 1):
            existing = dest.gallery.count()
            if existing >= options["num"] and not options["force"]:
                self.stdout.write(f"[{i}/{len(targets)}] {dest.name} — already has {existing} images, skipping")
                continue

            self.stdout.write(f"[{i}/{len(targets)}] Searching: {dest.name} ({dest.district or dest.province or 'Nepal'})")
            try:
                hits = search_destination_images(
                    dest, per_source=max(10, options["num"]),
                    min_score=options["min_score"], openverse_key=openverse_key,
                )
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  search error: {exc}")
                continue

            if not hits:
                self.stdout.write(self.style.WARNING("  no matching free images found"))
                continue

            saved = self._save_hits(dest, hits[: options["num"]], replace=options["force"])
            total_saved += saved
            self.stdout.write(self.style.SUCCESS(
                f"  saved {saved} images (top score {hits[0].match_score:.2f})"
            ))

        self.stdout.write(self.style.SUCCESS(f"Done. Saved {total_saved} images across {len(targets)} destinations."))

    def _collect_targets(self, options):
        if options["destination"]:
            val = options["destination"]
            d = (Destination.objects.filter(pk=val).first() if val.isdigit() else None) \
                or Destination.objects.filter(slug=val).first() \
                or Destination.objects.filter(name__icontains=val).first()
            return [d] if d else []
        if options["district"]:
            names = [n.strip() for n in options["district"].split(",") if n.strip()]
            qs = Destination.objects.none()
            for n in names:
                qs = qs | Destination.objects.filter(district__icontains=n) | \
                     Destination.objects.filter(name__icontains=n)
            return list(qs.distinct()[:500])
        if options["seed"]:
            out = []
            seen = set()
            for name in SEED_DESTINATIONS:
                d = Destination.objects.filter(name__icontains=name).first()
                if d and d.id not in seen:
                    seen.add(d.id)
                    out.append(d)
            return out
        if options["all"]:
            return list(Destination.objects.filter(is_active=True).iterator(chunk_size=200))
        return []

    @transaction.atomic
    def _save_hits(self, dest, hits, replace=False):
        if replace:
            # only replace web-sourced images, keep admin/AI ones
            dest.gallery.filter(source__in=[
                DestinationImage.Source.WIKIMEDIA,
                DestinationImage.Source.GOOGLE_PLACES,
                DestinationImage.Source.FOURSQUARE,
            ]).delete()

        existing_urls = set(
            dest.gallery.exclude(external_url="").values_list("external_url", flat=True)
        )
        saved = 0
        first = True
        for hit in hits:
            if hit.url in existing_urls:
                continue
            is_cover = first and not dest.cover_image
            img = DestinationImage.objects.create(
                destination=dest,
                external_url=hit.url,
                thumbnail_url=hit.thumbnail,
                caption=f"{dest.name} — {hit.title or hit.source}",
                source=self._map_source(hit.source),
                source_url=hit.source_page[:500] if hit.source_page else "",
                source_platform=hit.source,
                photographer=hit.author[:150],
                license_type=hit.license[:100],
                copyright_status="web_search",
                is_cover=is_cover,
                destination_match_score=round(hit.match_score, 3),
                authenticity_score=0.9 if hit.source == "wikimedia" else 0.75,
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_verified=True,
            )
            if is_cover:
                dest.gallery.filter(is_cover=True).exclude(id=img.id).update(is_cover=False)
                Destination.objects.filter(pk=dest.pk).update(cover_image=hit.url)
            existing_urls.add(hit.url)
            saved += 1
            first = False
        return saved

    @staticmethod
    def _map_source(src):
        return {
            "wikimedia": DestinationImage.Source.WIKIMEDIA,
            "openverse": DestinationImage.Source.UNSPLASH,
            "duckduckgo": DestinationImage.Source.ADMIN,
        }.get(src, DestinationImage.Source.ADMIN)
