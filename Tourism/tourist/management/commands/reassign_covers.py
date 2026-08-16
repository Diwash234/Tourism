"""
Management command: reassign_covers
====================================
Reassigns cover images and gallery photos for ALL Destinations using the
curated photo_catalog pools, so every attraction/hotel gets deterministic,
CATEGORY-CORRECT imagery (no more bike-on-temple, lion-on-mountain, beach-on-temple, etc.).

Usage:
    python manage.py reassign_covers --clear-first
    python manage.py reassign_covers --gallery-target 6
    python manage.py reassign_covers --only-missing
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination, DestinationImage
from tourist import photo_catalog


# Source enum shortcuts
SOURCE_REFERENCE = DestinationImage.Source.REFERENCE
SOURCE_UNSPLASH = DestinationImage.Source.UNSPLASH
SOURCE_FALLBACK = "fallback"

STATUS_APPROVED = DestinationImage.ImageStatus.APPROVED


def _source_key_for(url: str) -> str:
    if url.startswith("/images/"):
        return SOURCE_REFERENCE
    if "images.unsplash.com" in url:
        return SOURCE_UNSPLASH
    return SOURCE_FALLBACK


def _photo_to_row(dest: Destination, photo: dict, *, is_cover: bool) -> DestinationImage:
    url = photo.get("url", "")
    if not url:
        return None
    source = _source_key_for(url)
    author = photo.get("author", "") or ""
    caption = photo.get("caption", "") or (photo.get("tags", [""])[0] if photo.get("tags") else "") or ""
    license_type = photo.get("license", "")
    source_url = photo.get("source_url", "")
    authenticity = 0.95 if source == SOURCE_REFERENCE else 0.65
    return DestinationImage(
        destination=dest,
        external_url=url,
        thumbnail_url=photo.get("thumb", url) or url,
        caption=caption[:200],
        is_cover=is_cover,
        source=source,
        source_url=source_url[:500] if source_url else "",
        photographer=author[:150] if author else "",
        license_type=license_type[:100] if license_type else "",
        copyright_status="verified_reusable",
        image_category="cover" if is_cover else "gallery",
        verification_status=STATUS_APPROVED,
        is_verified=True,
        authenticity_score=authenticity,
        quality_score=0.8 if is_cover else 0.7,
        overall_score=authenticity,
        attribution=(f"{author} / {license_type}" if author else "").strip(" /"),
    )


class Command(BaseCommand):
    help = "Reassign deterministic, category-correct cover + gallery photos for all destinations."

    def add_arguments(self, parser):
        parser.add_argument("--gallery-target", type=int, default=6,
                            help="Number of gallery photos per destination (including cover). Default 6.")
        parser.add_argument("--only-missing", action="store_true",
                            help="Only assign to destinations that have no images yet.")
        parser.add_argument("--clear-first", action="store_true",
                            help="Delete ALL existing auto-assigned images first.")
        parser.add_argument("--limit", type=int, default=0,
                            help="Only process N destinations. 0 = all.")

    @transaction.atomic
    def handle(self, *args, **options):
        gallery_target = max(1, int(options["gallery_target"]))
        only_missing = bool(options["only_missing"])
        clear_first = bool(options["clear_first"])
        limit = int(options["limit"]) or 0

        self.stdout.write(self.style.MIGRATE_HEADING("Reassigning destination photos..."))
        self.stdout.write(f"  gallery-target = {gallery_target}")
        self.stdout.write(f"  only-missing   = {only_missing}")
        self.stdout.write(f"  clear-first    = {clear_first}")

        if clear_first:
            deleted, _ = DestinationImage.objects.filter(
                source__in=[SOURCE_UNSPLASH, SOURCE_REFERENCE, SOURCE_FALLBACK],
            ).delete()
            Destination.objects.update(cover_image=None)
            self.stdout.write(self.style.WARNING(f"  Cleared {deleted} existing auto-assigned image rows."))
        else:
            DestinationImage.objects.filter(
                source__in=[SOURCE_UNSPLASH, SOURCE_REFERENCE, SOURCE_FALLBACK],
                is_cover=True,
            ).update(is_cover=False)

        qs = Destination.objects.select_related("category").order_by("name")
        if limit:
            qs = qs[:limit]

        total = qs.count() if not limit else limit
        assigned_cover = 0
        added_gallery = 0
        skipped = 0
        new_rows = []

        for i, dest in enumerate(qs.iterator(), 1):
            existing_urls = set(
                DestinationImage.objects.filter(destination=dest)
                .exclude(external_url="")
                .values_list("external_url", flat=True)
            )

            if only_missing and existing_urls:
                skipped += 1
                continue

            try:
                cover = photo_catalog.resolve_cover_photo(dest)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  cover failed for {dest.name}: {exc}"))
                continue

            gallery = []
            try:
                gallery = photo_catalog.resolve_gallery_photos(dest, target=gallery_target - 1)
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f"  gallery failed for {dest.name}: {exc}"))

            seen = set(existing_urls)
            cover_url = cover.get("url", "")
            if cover_url and cover_url not in seen:
                row = _photo_to_row(dest, cover, is_cover=True)
                if row:
                    new_rows.append(row)
                    seen.add(cover_url)
                    assigned_cover += 1
            elif cover_url:
                DestinationImage.objects.filter(destination=dest, external_url=cover_url).update(is_cover=True)

            for photo in gallery:
                url = photo.get("url", "")
                if not url or url in seen or url == cover_url:
                    continue
                row = _photo_to_row(dest, photo, is_cover=False)
                if row:
                    new_rows.append(row)
                    seen.add(url)
                    added_gallery += 1

            if i % 500 == 0:
                self.stdout.write(f"  ...processed {i}/{total}  (batch rows: {len(new_rows)})")
                DestinationImage.objects.bulk_create(new_rows, ignore_conflicts=False, batch_size=500)
                new_rows = []

        if new_rows:
            DestinationImage.objects.bulk_create(new_rows, ignore_conflicts=False, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"\n  Done. Processed {total} destinations. "
            f"Covers assigned: {assigned_cover}. Gallery rows added: {added_gallery}. Skipped: {skipped}."
        ))

        total_dests = Destination.objects.count()
        with_cover = Destination.objects.filter(gallery__is_cover=True).distinct().count()
        total_imgs = DestinationImage.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"  Final state: {total_dests} destinations, {with_cover} with covers, {total_imgs} total images."
        ))
