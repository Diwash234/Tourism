"""Backfill missing destination media from the verified public seed.

Only destinations with no usable gallery image are changed. Matching is by
stable slug first, then exact normalized name. Existing media and admin
corrections are never overwritten.
"""
from __future__ import annotations

import gzip
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import connection
from tourist.models import Destination, DestinationImage


ARCHIVE = Path(settings.BASE_DIR).parent / "downloads" / "nepal-tourism-seed.sqlite3.gz"


class Command(BaseCommand):
    help = "Backfill missing destination media from the verified public seed."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write("Media seed sync is intended for PostgreSQL; skipping.")
            return
        if not ARCHIVE.is_file():
            raise CommandError(f"Seed archive not found: {ARCHIVE}")

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            sqlite_path = Path(tmp.name)
        try:
            with gzip.open(ARCHIVE, "rb") as src, sqlite_path.open("wb") as dst:
                dst.write(src.read())

            previous = connection.settings_dict.get("NAME")
            connection.close()
            settings.DATABASES["default"]["NAME"] = str(sqlite_path)
            connection.settings_dict["NAME"] = str(sqlite_path)
            try:
                source_rows = list(
                    DestinationImage.objects.filter(
                        destination__isnull=False,
                        external_url__gt="",
                    ).values(
                        "destination__slug", "destination__name", "external_url",
                        "caption", "is_cover", "verification_status", "source",
                        "source_url", "source_platform", "photographer",
                        "license_type", "copyright_status", "alt_text",
                    )
                )
            finally:
                connection.close()
                settings.DATABASES["default"]["NAME"] = previous
                connection.settings_dict["NAME"] = previous

            by_slug = {}
            by_name = {}
            for row in source_rows:
                by_slug.setdefault(row["destination__slug"], []).append(row)
                key = " ".join((row["destination__name"] or "").casefold().split())
                by_name.setdefault(key, []).append(row)

            created = 0
            covers = 0
            for destination in Destination.objects.all().iterator():
                has_media = destination.gallery.filter(
                    external_url__gt=""
                ).exists() or destination.gallery.filter(
                    image__isnull=False
                ).exclude(image="").exists()
                if has_media:
                    continue
                rows = by_slug.get(destination.slug) or by_name.get(
                    " ".join((destination.name or "").casefold().split()), []
                )
                if not rows:
                    continue
                for row in rows[:6]:
                    image = DestinationImage.objects.create(
                        destination=destination,
                        external_url=row["external_url"],
                        caption=row["caption"] or destination.name,
                        is_cover=bool(row["is_cover"]),
                        verification_status=row["verification_status"] or DestinationImage.ImageStatus.APPROVED,
                        source=row["source"] or DestinationImage.Source.ADMIN,
                        source_url=row["source_url"] or "",
                        source_platform=row["source_platform"] or "",
                        photographer=row["photographer"] or "",
                        license_type=row["license_type"] or "",
                        copyright_status=row["copyright_status"] or "",
                        alt_text=row["alt_text"] or destination.name,
                    )
                    created += 1
                    if image.is_cover:
                        covers += 1
                cover = destination.gallery.filter(is_cover=True, external_url__gt="").first()
                if cover and not str(destination.cover_image or "").strip():
                    Destination.objects.filter(pk=destination.pk).update(
                        cover_image=cover.external_url
                    )
            self.stdout.write(self.style.SUCCESS(
                f"Destination media seed sync: created={created}, covers={covers}"
            ))
        finally:
            sqlite_path.unlink(missing_ok=True)
