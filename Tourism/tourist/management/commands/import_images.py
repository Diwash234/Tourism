"""
Tourism/tourist/management/commands/import_images.py

Import image METADATA from the standalone image server into the database.

The actual image binaries are NEVER read into Django/SQLite — they stay on the
image server (dev: `python -m http.server`, prod: Nginx). This command only
records the relative path + metadata on DestinationImage so the API can return
`IMAGE_BASE_URL + /images/ + image_path` URLs.

Usage (from Tourism/, where manage.py lives):
    python manage.py import_images
    python manage.py import_images ./image-server/images
    python manage.py import_images --dry-run
    python manage.py import_images --link-by name
    python manage.py import_images --base-url https://images.example.com
    python manage.py import_images --cover --max-per-destination 10

Matching rules (in order):
    1. Path folder matches a destination slug or name
       (e.g. images/nepal/kathmandu/001.webp  ->  destination slug "kathmandu").
    2. File-name prefix matches a destination slug or name
       (e.g. kathmandu_001.webp / kathmandu-001.webp  ->  "kathmandu").
    3. Otherwise the file is reported as unmatched (no rows are created).

Duplicates are skipped: an existing DestinationImage with the same
(destination, image_path) is left untouched.
"""
import os
import posixpath

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from tourist.image_server import (
    SUPPORTED_EXTENSIONS,
    guess_alt_text,
    image_server_url,
    normalize_image_path,
)
from tourist.models import Destination, DestinationImage


class Command(BaseCommand):
    help = "Import image metadata (paths/URLs, not binaries) from the standalone image server directory."

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default=None,
                            help="Root of the image dataset (default: settings.IMAGE_SERVER_ROOT)")
        parser.add_argument("--dry-run", action="store_true",
                            help="Scan and report what WOULD be imported without writing anything")
        parser.add_argument("--base-url", default=None,
                            help="Override IMAGE_BASE_URL for URL generation (e.g. https://images.example.com)")
        parser.add_argument("--link-by", choices=["slug", "name"], default="slug",
                            help="Match folders/file prefixes against destination slugs (default) or names")
        parser.add_argument("--cover", action="store_true",
                            help="Set the first imported image of each destination as its cover")
        parser.add_argument("--max-per-destination", type=int, default=None,
                            help="Only import up to N images per destination (sorted by filename)")
        parser.add_argument("--set-ordering", action="store_true",
                            help="Write a sequential ordering number into each imported row")

    def handle(self, *args, **options):
        root = os.path.abspath(options["path"] or settings.IMAGE_SERVER_ROOT)
        if not os.path.isdir(root):
            self.stderr.write(self.style.ERROR(
                f"Image root not found: {root}\n"
                f"Place your dataset under image-server/images/ (see docs/IMAGE_SERVER.md) "
                f"or pass an explicit path."
            ))
            raise SystemExit(1)

        self.stdout.write(f"Scanning {root} ...")
        files = self._scan(root)
        if not files:
            self.stderr.write(self.style.WARNING("No supported image files found."))
            return
        self.stdout.write(f"Found {len(files)} supported image files.")

        # ---- destination lookup tables ----
        dests = list(Destination.objects.filter(is_active=True))
        by_slug = {}
        by_name = {}
        for d in dests:
            by_slug.setdefault((d.slug or "").lower(), d)
            by_name.setdefault((d.name or "").strip().lower(), d)
        self.stdout.write(f"Destinations available for matching: {len(dests)}")

        # ---- match ----
        import re
        prefix_re = re.compile(r"^([a-z0-9][a-z0-9 _-]*?)[ _-]?\d+", re.I)

        matched = {}   # dest_id -> list of (relpath, alt)
        unmatched = []
        for rel in files:
            dest = self._match_destination(rel, by_slug, by_name, options["link_by"], prefix_re)
            if dest is None:
                unmatched.append(rel)
                continue
            matched.setdefault(dest.id, []).append(rel)

        self.stdout.write(f"Matched: {len(matched)} destinations, "
                          f"{sum(len(v) for v in matched.values())} files. "
                          f"Unmatched: {len(unmatched)} files.")

        if options["dry_run"]:
            self._report(matched, unmatched, options, dry_run=True)
            return

        # ---- apply ----
        created, updated, skipped, no_dupe = 0, 0, 0, 0
        with transaction.atomic():
            for dest_id, rels in sorted(matched.items()):
                dest = Destination.objects.get(pk=dest_id)
                if options["max_per_destination"]:
                    rels = sorted(rels)[: options["max_per_destination"]]
                for order, rel in enumerate(sorted(rels), start=1):
                    image_path = normalize_image_path(rel)
                    alt = guess_alt_text(rel, fallback=dest.name)
                    exists = DestinationImage.objects.filter(
                        destination=dest, image_path=image_path
                    ).first()
                    if exists:
                        no_dupe += 1
                        continue
                    photo = DestinationImage(
                        destination=dest,
                        image_path=image_path,
                        external_url=image_server_url(image_path),
                        thumbnail_url=image_server_url(image_path),
                        alt_text=alt,
                        ordering=order if options["set_ordering"] else 0,
                        caption=alt[:200],
                        is_cover=False,
                        source=DestinationImage.Source.IMAGE_SERVER,
                        source_platform="Image Server",
                        copyright_status="image_server",
                        verification_status=DestinationImage.ImageStatus.APPROVED,
                        is_verified=True,
                    )
                    photo.save()
                    created += 1
            # optional covers: first image per destination
            if options["cover"]:
                for dest_id in matched:
                    first = DestinationImage.objects.filter(
                        destination_id=dest_id, source=DestinationImage.Source.IMAGE_SERVER
                    ).order_by("ordering", "id").first()
                    if first:
                        DestinationImage.objects.filter(destination_id=dest_id).update(is_cover=False)
                        first.is_cover = True
                        first.save(update_fields=["is_cover"])
                        updated += 1

        self._report(matched, unmatched, options, created=created, updated=updated,
                     skipped=skipped, no_dupe=no_dupe)

    # ------------------------------------------------------------------ utils
    def _scan(self, root):
        files = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in sorted(filenames):
                if fn.startswith(".") or fn == ".gitkeep":
                    continue
                ext = os.path.splitext(fn)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    rel = os.path.relpath(os.path.join(dirpath, fn), root)
                    files.append(rel.replace(os.sep, "/"))
        return files

    def _match_destination(self, rel, by_slug, by_name, link_by, prefix_re):
        parts = posixpath.normpath(rel).split("/")
        folder = parts[-2] if len(parts) >= 2 else ""
        stem = posixpath.splitext(parts[-1])[0]

        candidates = []
        if folder:
            candidates.append(folder)
        m = prefix_re.match(stem)
        if m:
            candidates.append(m.group(1).strip().strip("_-"))
        candidates.append(stem)

        tables = {"slug": by_slug, "name": by_name}
        table = tables[link_by]
        for cand in candidates:
            if not cand:
                continue
            d = table.get(cand.strip().lower())
            if d:
                return d
        return None

    def _report(self, matched, unmatched, options, dry_run=False,
                created=0, updated=0, skipped=0, no_dupe=0):
        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing was written."))
            self.stdout.write(f"Would create ~{sum(len(v) for v in matched.values())} rows across "
                              f"{len(matched)} destinations.")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Done. Created: {created} | Covers set: {updated} | "
                f"Duplicates skipped: {no_dupe} | Unmatched: {len(unmatched)}"
            ))
        if unmatched:
            self.stdout.write(self.style.WARNING(f"Unmatched files ({len(unmatched)}):"))
            for rel in unmatched[:20]:
                self.stdout.write(f"   {rel}")
            if len(unmatched) > 20:
                self.stdout.write(f"   ... and {len(unmatched) - 20} more")
        self.stdout.write("")
        self.stdout.write(
            "Tip: URL format is IMAGE_BASE_URL + /images/ + image_path, e.g. "
            + image_server_url("nepal/kathmandu/001.webp")
        )
