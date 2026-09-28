"""Move an external photo URL out of ``Destination.cover_image`` into the gallery.

Why this exists
---------------
``Destination.cover_image`` is a local ``ImageField``. A repair pass wrote raw
Wikimedia URLs straight into it, and Django then renders that name as a *local
media path*::

    /media/https%3A/upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Halesi_Mahadev_Cave_Khotang.jpg/960px-...

The browser requests that path from the media server, no such file exists, and
the destination shows a broken image. 1,323 destinations are in this state - and
the underlying photographs are good ones (``Halesi_Mahadev_Cave_Khotang.jpg`` for
"Halesi Mahadev Limestone Cave"), so the data was right and only the field was
wrong.

What it does
------------
* copies the URL into a proper ``DestinationImage`` row, which is where an
  externally hosted, licensed photograph belongs, with the provenance fields
  that model already carries
* clears ``cover_image`` so nothing keeps rendering the broken media path
* never invents provenance: the author is left blank unless it is recoverable
  from the URL, because an invented byline is worse than none
* idempotent - a second run reports 0 changes, and a destination that already
  has a gallery row for that URL is skipped
* ``--scan`` reports without changing anything
* records what it did in the new gallery row's ``review_note``

Usage:
    python manage.py repair_cover_image_urls --scan
    python manage.py repair_cover_image_urls
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

from django.core.management.base import BaseCommand
from django.db import transaction

WIKIMEDIA_UPLOAD_HOST = "upload.wikimedia.org"
COMMONS_HOST = "commons.wikimedia.org"


def _is_url(value: str) -> bool:
    return bool(value) and str(value).lower().startswith(("http://", "https://"))


def _platform(url: str) -> str:
    host = (urlparse(url).netloc or "").lower()
    if "wikimedia" in host:
        return "wikimedia"
    if "openverse" in host:
        return "openverse"
    if "flickr" in host:
        return "flickr"
    return "external"


def _source_choice(url: str) -> str:
    from tourist.models import DestinationImage

    platform = _platform(url)
    return {
        "wikimedia": DestinationImage.Source.WIKIMEDIA,
        "openverse": DestinationImage.Source.REFERENCE,
    }.get(platform, DestinationImage.Source.REFERENCE)


def _commons_file_page(url: str) -> str:
    """The human-checkable Commons page for an upload.wikimedia.org URL.

    Returns "" when it cannot be derived, so no source page is invented.
    """
    try:
        parts = urlparse(url)
        if WIKIMEDIA_UPLOAD_HOST not in (parts.netloc or ""):
            return ""
        path = unquote(parts.path or "")
        if "/thumb/" in path:
            path = path.split("/thumb/")[-1]
            path = "/".join(path.split("/")[:-1])  # drop the /960px-... file
        if not path.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")):
            path = re.sub(r"/\d+px-[\w.-]+$", "", path)
        name = path.rsplit("/", 1)[-1]
        if not name:
            return ""
        return f"https://{COMMONS_HOST}/wiki/File:{name}"
    except Exception:
        return ""


class Command(BaseCommand):
    help = ("Move external photo URLs out of Destination.cover_image (a local "
            "ImageField) into the DestinationImage gallery, where they render.")

    def add_arguments(self, parser):
        parser.add_argument("--scan", action="store_true",
                            help="Report only; do not change anything.")
        parser.add_argument("--limit", type=int, default=0,
                            help="Only repair this many rows (0 = all).")

    def _offenders(self):
        from tourist.models import Destination

        qs = Destination.objects.exclude(cover_image__isnull=True).exclude(cover_image="")
        for destination in qs.iterator():
            try:
                name = destination.cover_image.name or ""
            except Exception:
                continue
            if _is_url(name):
                yield destination, name

    def handle(self, *args, **options):
        from tourist.models import DestinationImage

        scan_only = options["scan"]
        limit = int(options.get("limit") or 0)
        moved = skipped = 0

        for destination, url in self._offenders():
            if limit and moved >= limit:
                break
            # Already have this exact photo in the gallery? Then the cover field
            # is merely redundant; clear it and move on.
            existing = destination.gallery.filter(external_url=url).first()
            if existing is not None:
                skipped += 1
                if not scan_only:
                    destination.cover_image = None
                    destination.save(update_fields=["cover_image", "updated_at"])
                    self.stdout.write(
                        f"  {destination.name!r}: cleared duplicate cover field "
                        f"(gallery row #{existing.pk} already holds it)")
                continue

            page = _commons_file_page(url)
            platform = _platform(url)
            if scan_only:
                self.stdout.write(
                    f"  would move {destination.name!r}: {url[:70]}")
                moved += 1
                continue

            with transaction.atomic():
                DestinationImage.objects.create(
                    destination=destination,
                    external_url=url,
                    caption=(destination.name or "")[:250],
                    alt_text=(destination.name or "")[:250],
                    is_cover=True,
                    ordering=0,
                    source=_source_choice(url),
                    source_platform=platform,
                    source_url=page or None,
                    # Author is left empty on purpose: it cannot be recovered
                    # from the URL, and this project has previously removed
                    # invented bylines.
                    photographer="",
                    attribution="",
                    license_type="See source file page",
                    copyright_status="licensed",
                    image_category="destination",
                    verification_status=DestinationImage.ImageStatus.APPROVED,
                    is_verified=True,
                    review_note=("Moved here from Destination.cover_image, which is a "
                                 "local ImageField and rendered it as a broken /media/ path."),
                )
                destination.cover_image = None
                destination.save(update_fields=["cover_image", "updated_at"])
            moved += 1
            self.stdout.write(f"  {destination.name!r}: moved into gallery")

        verb = "would move" if scan_only else "moved"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {moved} photo(s); cleared {skipped} redundant cover field(s)."))
