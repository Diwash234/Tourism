"""Backfill missing destination media from the verified public seed.

Extracts authentic imagery directly from the bundled seed archive using Python's
built-in SQLite reader, avoiding engine conflicts on PostgreSQL deployments.
Only destinations with no usable gallery image are changed.
Matching is by stable slug first, then exact normalized name.
Existing media and admin corrections are never overwritten.
"""
from __future__ import annotations

import gzip
import sqlite3
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from tourist.models import Destination, DestinationImage


ARCHIVE = Path(settings.BASE_DIR).parent / "downloads" / "nepal-tourism-seed.sqlite3.gz"


class Command(BaseCommand):
    help = "Backfill missing destination media from the verified public seed."

    def handle(self, *args, **options):
        if not ARCHIVE.is_file():
            raise CommandError(f"Seed archive not found: {ARCHIVE}")

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            sqlite_path = Path(tmp.name)
        try:
            with gzip.open(ARCHIVE, "rb") as src, sqlite_path.open("wb") as dst:
                dst.write(src.read())

<<<<<<< HEAD
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
                        "license_type", "copyright_status", "alt_text", "is_verified",
                    )
                )
            finally:
                connection.close()
                settings.DATABASES["default"]["NAME"] = previous
                connection.settings_dict["NAME"] = previous
=======
            conn = sqlite3.connect(str(sqlite_path))
            cur = conn.cursor()
            cur.execute("""
                SELECT d.slug, d.name, di.external_url, di.caption, di.is_cover,
                       di.verification_status, di.source, di.source_url, di.source_platform,
                       di.photographer, di.license_type, di.copyright_status, di.alt_text
                FROM tourist_destinationimage di
                JOIN tourist_destination d ON di.destination_id = d.id
                WHERE di.external_url IS NOT NULL AND di.external_url != ''
            """)
            raw_rows = cur.fetchall()
            conn.close()
>>>>>>> origin/arena/01a0ed99-tourism

            by_slug = {}
            by_name = {}
            for r in raw_rows:
                slug, name, ext_url, caption, is_cover, ver_status, source, src_url, src_plat, photo_auth, lic, copyr, alt = r
                row_dict = {
                    "slug": slug,
                    "name": name,
                    "external_url": ext_url,
                    "caption": caption,
                    "is_cover": bool(is_cover),
                    "verification_status": ver_status,
                    "source": source,
                    "source_url": src_url,
                    "source_platform": src_plat,
                    "photographer": photo_auth,
                    "license_type": lic,
                    "copyright_status": copyr,
                    "alt_text": alt,
                }
                by_slug.setdefault(slug, []).append(row_dict)
                key = " ".join((name or "").casefold().split())
                by_name.setdefault(key, []).append(row_dict)

            created = 0
            covers = 0
            for destination in Destination.objects.all().iterator(chunk_size=500):
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
<<<<<<< HEAD
                        verification_status=row["verification_status"] or DestinationImage.ImageStatus.APPROVED,
                        is_verified=bool(row.get("is_verified", True)),
=======
                        is_verified=True,
                        verification_status=DestinationImage.ImageStatus.APPROVED,
>>>>>>> origin/arena/01a0ed99-tourism
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
