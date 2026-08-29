"""
Generate/fetch 10-20 images for every Destination, Hotel and Hospital
using the multi-source collector (AI Flux generation + free web search).

No paid API or billing required.

Usage:
    python manage.py generate_all_images                  # everything
    python manage.py generate_all_images --kind destination
    python manage.py generate_all_images --kind hotel --num 8
    python manage.py generate_all_images --kind hospital
    python manage.py generate_all_images --destination nagarkot --num 15
    python manage.py generate_all_images --force            # replace existing
    python manage.py generate_all_images --no-ai            # web search only
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination, DestinationImage, Hotel, Hospital
from tourist.services.image_generation.collector import (
    collect_for_destination, collect_for_hotel, collect_for_hospital,
)


class Command(BaseCommand):
    help = "Generate/fetch AI + web images for all destinations, hotels and hospitals."

    def add_arguments(self, parser):
        parser.add_argument("--kind", choices=["destination", "hotel", "hospital", "all"], default="all")
        parser.add_argument("--destination", help="single destination id/slug/name")
        parser.add_argument("--num", type=int, default=14)
        parser.add_argument("--force", action="store_true", help="replace existing gallery images")
        parser.add_argument("--no-ai", action="store_true", help="skip AI generation (web search only)")
        parser.add_argument("--limit", type=int, default=0, help="only process first N rows (for testing)")

    def handle(self, *args, **options):
        n = options["num"]
        use_ai = not options["no_ai"]
        total = 0

        if options["kind"] in ("all", "destination"):
            if options["destination"]:
                v = options["destination"]
                dest = (Destination.objects.filter(pk=v).first() if v.isdigit() else None) \
                    or Destination.objects.filter(slug=v).first() \
                    or Destination.objects.filter(name__icontains=v).first()
                targets = [dest] if dest else []
            else:
                targets = list(Destination.objects.filter(is_active=True))
            if options["limit"]:
                targets = targets[: options["limit"]]
            total += self._process(
                "Destinations", targets,
                lambda d: collect_for_destination(d, num=n, use_ai=use_ai),
                options["force"],
            )

        if options["kind"] in ("all", "hotel"):
            hotels = list(Hotel.objects.select_related("destination").all())
            if options["limit"]:
                hotels = hotels[: options["limit"]]
            total += self._process(
                "Hotels", hotels,
                lambda h: collect_for_hotel(h, num=min(n, 8)), options["force"],
            )

        if options["kind"] in ("all", "hospital"):
            hospitals = list(Hospital.objects.all())
            if options["limit"]:
                hospitals = hospitals[: options["limit"]]
            total += self._process(
                "Hospitals", hospitals,
                lambda hp: collect_for_hospital(hp, num=6), options["force"],
            )

        self.stdout.write(self.style.SUCCESS(f"Done. Saved {total} images."))

    def _process(self, label, queryset, collector, force):
        saved_total = 0
        for i, obj in enumerate(queryset, 1):
            try:
                images = collector(obj)
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  {obj}: collector error {exc}")
                continue
            if not images:
                continue
            saved = self._save(obj, images, force)
            saved_total += saved
            if i % 50 == 0 or saved:
                self.stdout.write(f"[{label} {i}/{len(queryset)}] {str(obj)[:40]:40} +{saved} (total {saved_total})")
        return saved_total

    @transaction.atomic
    def _save(self, obj, images, force):
        if isinstance(obj, Destination):
            qs = obj.gallery
            cover_field = "cover_image"
        elif isinstance(obj, Hotel):
            qs = obj.destination.gallery if obj.destination_id else None
            cover_field = None
        else:  # Hospital — create a Destination-like? Hospitals have no gallery; skip
            return 0
        if qs is None:
            return 0

        if force:
            qs.filter(source=DestinationImage.Source.AI_GENERATED).delete()

        existing = set(qs.exclude(external_url="").values_list("external_url", flat=True))
        saved = 0
        first = True
        for img in images:
            if img["url"] in existing:
                continue
            is_cover = first and (isinstance(obj, Destination) and not obj.cover_image)
            di = DestinationImage(
                destination=obj if isinstance(obj, Destination) else obj.destination,
                external_url=img["url"],
                thumbnail_url=img.get("thumbnail", img["url"]),
                caption=img.get("caption", "")[:200],
                source=self._map_source(img.get("source")),
                source_platform=img.get("source_platform", "")[:100],
                photographer=img.get("photographer", ""),
                license_type=img.get("license", ""),
                copyright_status="ai_generated" if img.get("source") == "ai_generated" else "web_search",
                generation_prompt=img.get("prompt", ""),
                generation_seed=img.get("seed"),
                generation_provider="flux-pollinations" if img.get("source") == "ai_generated" else "",
                destination_match_score=img.get("match_score"),
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_cover=is_cover,
            )
            di.save()
            if is_cover and isinstance(obj, Destination):
                qs.filter(is_cover=True).exclude(id=di.id).update(is_cover=False)
                Destination.objects.filter(pk=obj.pk).update(cover_image=img["url"])
            existing.add(img["url"])
            saved += 1
            first = False
        return saved

    @staticmethod
    def _map_source(s):
        return {
            "wikimedia": DestinationImage.Source.WIKIMEDIA,
            "web": DestinationImage.Source.ADMIN,
            "ai_generated": DestinationImage.Source.AI_GENERATED,
        }.get(s, DestinationImage.Source.ADMIN)
