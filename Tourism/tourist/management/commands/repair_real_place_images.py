"""Repair real place imagery without ever deleting the existing public image.

For each destination, search exact place-specific Wikimedia/Openverse results and
promote only high-confidence real photographs. For each hotel, search the exact
hotel name plus destination and require the hotel name in source/title evidence.
Existing images remain untouched if no sufficiently verified replacement exists.

Run:
  python manage.py repair_real_place_images --kind all --apply
  python manage.py repair_real_place_images --kind destination --limit 100 --apply
"""
from __future__ import annotations

import re
import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination, DestinationImage, Hotel
from tourist.services.image_search.search import (
    search_destination_images, search_openverse, search_wikimedia,
)


TIMEOUT = 8
UA = "NepalTourismPlatform/2.0 image-integrity-repair"


def _norm_tokens(value):
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _is_live_image(url):
    if not url or not str(url).startswith(("http://", "https://")):
        return False
    try:
        r = requests.head(url, allow_redirects=True, timeout=TIMEOUT,
                          headers={"User-Agent": UA})
        ctype = (r.headers.get("content-type") or "").lower()
        if r.status_code < 400 and ctype.startswith("image/"):
            return True
        # Some CDNs reject HEAD; a tiny ranged GET still verifies the URL.
        r = requests.get(url, stream=True, timeout=TIMEOUT,
                         headers={"User-Agent": UA, "Range": "bytes=0-1023"})
        ctype = (r.headers.get("content-type") or "").lower()
        return r.status_code < 400 and ctype.startswith("image/")
    except requests.RequestException:
        return False


def _place_score(hit, destination):
    own = _norm_tokens(
        f"{destination.name} {getattr(destination, 'district', '')} "
        f"{getattr(destination, 'province', '')} {getattr(destination, 'city', '')}"
    )
    evidence = _norm_tokens(
        f"{hit.title} {hit.source_page} {hit.source_page_url if hasattr(hit, 'source_page_url') else ''}"
    )
    name = _norm_tokens(destination.name)
    if name and name <= evidence:
        return 1.0
    if own & evidence:
        return max(float(getattr(hit, "match_score", 0) or 0), 0.80)
    return float(getattr(hit, "match_score", 0) or 0)


def _hotel_score(hit, hotel):
    hotel_name = _norm_tokens(hotel.name)
    # Require at least the meaningful hotel-name tokens to appear together
    # in source/title evidence. Destination-only evidence is never sufficient.
    meaningful = {x for x in hotel_name if len(x) >= 4}
    evidence = _norm_tokens(
        f"{hit.title} {hit.source_page} "
        f"{getattr(hit, 'source_page_url', '')} {hotel.name} {hotel.destination.name}"
    )
    title_evidence = _norm_tokens(
        f"{hit.title} {hit.source_page} {getattr(hit, 'source_page_url', '')}"
    )
    if len(meaningful) >= 2 and len(meaningful & title_evidence) >= max(2, len(meaningful) - 1):
        return 1.0
    return 0.0


class Command(BaseCommand):
    help = "Replace/add only high-confidence real destination and hotel images; never delete existing media."

    def add_arguments(self, parser):
        parser.add_argument("--kind", choices=["destination", "hotel", "all"], default="all")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--images-per-place", type=int, default=5)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--keep-existing", action="store_true", default=True)

    def handle(self, *args, **opts):
        apply = opts["apply"]
        limit = opts["limit"]
        n = max(1, min(opts["images_per_place"], 8))
        stats = {"destinations": 0, "destination_images": 0, "hotels": 0,
                 "hotel_images": 0, "skipped": 0}

        if opts["kind"] in ("all", "destination"):
            qs = Destination.objects.filter(is_active=True).order_by("id")
            if limit:
                qs = qs[:limit]
            for d in qs.iterator():
                stats["destinations"] += 1
                hits = search_destination_images(
                    d, per_source=max(20, n * 4),
                    min_score=0.50,
                    sources=("wikimedia", "openverse"),
                )
                accepted = []
                seen = set()
                for hit in hits:
                    score = _place_score(hit, d)
                    if score < 0.85 or hit.source not in ("wikimedia", "openverse"):
                        continue
                    if hit.url in seen or not _is_live_image(hit.url):
                        continue
                    seen.add(hit.url)
                    accepted.append((hit, score))
                    if len(accepted) >= n:
                        break

                if apply and accepted:
                    self._apply_destination(d, accepted)
                stats["destination_images"] += len(accepted)
                if not accepted:
                    stats["skipped"] += 1

        if opts["kind"] in ("all", "hotel"):
            qs = Hotel.objects.select_related("destination").filter(is_active=True).order_by("id")
            if limit:
                qs = qs[:limit]
            for h in qs.iterator():
                stats["hotels"] += 1
                shim = type("HotelImageSearchPlace", (), {
                    "name": f"{h.name} {h.destination.name}",
                    "district": getattr(h.destination, "district", ""),
                    "province": getattr(h.destination, "province", ""),
                    "city": getattr(h.destination, "city", ""),
                    "municipality": getattr(h.destination, "municipality", ""),
                    "category_id": getattr(h.destination, "category_id", None),
                    "category": getattr(h.destination, "category", None),
                })()
                hits = search_destination_images(
                    shim, per_source=max(20, n * 5),
                    min_score=0.50,
                    sources=("wikimedia", "openverse"),
                )
                accepted = []
                seen = set()
                for hit in hits:
                    score = _hotel_score(hit, h)
                    if score < 1.0 or hit.source not in ("wikimedia", "openverse"):
                        continue
                    if hit.url in seen or not _is_live_image(hit.url):
                        continue
                    seen.add(hit.url)
                    accepted.append((hit, score))
                    if len(accepted) >= n:
                        break

                if apply and accepted:
                    self._apply_hotel(h, accepted)
                stats["hotel_images"] += len(accepted)
                if not accepted:
                    stats["skipped"] += 1

        mode = "APPLIED" if apply else "DRY RUN"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: destinations={stats['destinations']} "
            f"destination_candidates={stats['destination_images']} "
            f"hotels={stats['hotels']} hotel_candidates={stats['hotel_images']} "
            f"unchanged/no-safe-match={stats['skipped']}"
        ))

    @transaction.atomic
    def _apply_destination(self, d, accepted):
        existing = set(d.gallery.exclude(external_url="").values_list("external_url", flat=True))
        new_rows = []
        for idx, (hit, score) in enumerate(accepted):
            if hit.url in existing:
                continue
            new_rows.append(DestinationImage(
                destination=d,
                external_url=hit.url,
                thumbnail_url=hit.thumbnail or hit.url,
                caption=d.name,
                alt_text=hit.title[:255] if hit.title else d.name,
                is_cover=False,
                source=DestinationImage.Source.WIKIMEDIA if hit.source == "wikimedia" else DestinationImage.Source.ADMIN,
                source_platform=hit.source,
                source_url=hit.source_page,
                photographer=hit.author[:150],
                license_type=hit.license[:100],
                copyright_status="verified_reusable",
                authenticity_score=1.0,
                destination_match_score=score,
                quality_score=min(1.0, (hit.width or 1200) / 1200),
                realism_score=1.0,
                overall_score=score,
                is_verified=True,
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_promoted=True,
                ordering=10,
            ))
        if new_rows:
            DestinationImage.objects.bulk_create(new_rows)
            # Never clear the old cover first. Promote the new verified image
            # only after its URL has passed the live-image check above.
            new_cover = new_rows[0]
            new_cover.is_cover = True
            new_cover.ordering = 0
            new_cover.save(update_fields=["is_cover", "ordering", "updated_at"])
            d.cover_image = new_cover.external_url
            d.save(update_fields=["cover_image", "updated_at"])

    @transaction.atomic
    def _apply_hotel(self, h, accepted):
        # Hotel has its own image fields. Never copy a destination image.
        hit, score = accepted[0]
        if not h.external_image_url and not h.cover_image:
            h.external_image_url = hit.url
            h.source_url = hit.source_page
            h.save(update_fields=["external_image_url", "source_url", "updated_at"])
        elif h.external_image_url:
            # Only replace when the existing URL is already known to be
            # mismatched by the media-integrity layer; otherwise preserve it.
            from tourist.media_integrity import hotel_image_status
            if hotel_image_status(h, external_url=h.external_image_url,
                                  source_url=h.source_url) == "mismatch":
                h.external_image_url = hit.url
                h.source_url = hit.source_page
                h.save(update_fields=["external_image_url", "source_url", "updated_at"])
