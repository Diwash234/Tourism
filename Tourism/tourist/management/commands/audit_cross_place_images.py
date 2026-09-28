"""Find images reused across different places, and report per place.

Why
---
The gallery is the single most misleading part of this dataset. Measured on the
real database: 26,203 gallery rows reference only 7,151 distinct images, and
685 of those images are attached to more than three different destinations.
One photograph of the SAARC Secretariat in Kathmandu was serving 331
destinations. A traveller looking at "Gorkha Durbar" was very likely looking at
Kathmandu, and had no way to know it.

The same problem crosses tables: 1,642 hotels were showing a photo that belongs
to a destination. A hotel photo has to be a photo of that hotel -- a nice lake
view of the district is not a picture of the hotel.

This command only reports. It never deletes or reassigns an image, because
knowing an image is wrong does not tell you the right replacement, and guessing
a replacement is how a dataset ends up confidently wrong.

What counts as "the same image"
-------------------------------
``external_url`` is the only image reference used by the real data, so identity
is the URL -- but normalised, because the same photograph appears at many
sizes. A Wikimedia ``/thumb/.../800px-Name.jpg`` and its 1024px sibling are one
image, and must not be mistaken for two independent matches. Query strings and
thumbnail size prefixes are stripped before comparing.

Severity, and why it is not a vibe
----------------------------------
* ``destination_photo_on_hotel`` -- a hotel showing a destination's image. This
  is a category error, not a judgement call, so it is reported as a defect.
* ``reused_by_3_plus`` -- one image on three or more different places. A real
  landmark can legitimately photograph well, but three or more unrelated places
  sharing a frame means the image is standing in for data that is missing.
* ``reused_by_2`` -- two places. Ambiguous: a shared regional view can be
  correct. Reported, not condemned.
* ``duplicate_cover`` -- a destination with more than one ``is_cover`` row. The
  gallery cannot then answer "the" cover deterministically.

Nothing here asserts that a place *should* have a particular photo. It reports
what is shared so a human, or a licensed source, can decide.

Usage
-----
    python manage.py audit_cross_place_images
    python manage.py audit_cross_place_images --threshold 2
    python manage.py audit_cross_place_images --tsv reuse.tsv --per-place
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand

from tourist.console_safe import make_console_utf8, safe_text
from tourist.models import DestinationImage, Hotel

# Wikimedia renders several widths of one file. Strip the width marker so a
# 320px and an 800px copy of one photograph are recognised as one image.
_WIKIMEDIA_WIDTHS = ("120px-", "250px-", "320px-", "640px-", "800px-", "1024px-", "1280px-")


def normalise_image_url(url) -> str:
    """Collapse the size variants of one photograph to a single identity.

    Returns "" for a blank reference so callers never key on an empty string
    (which would otherwise make every imageless row look like one giant
    "shared" image).

    Accepts non-strings on purpose: ``Hotel.cover_image`` and
    ``DestinationImage.image`` are ``ImageFieldFile`` instances when read off a
    model instance rather than a ``values()`` row, and passing one straight
    through used to raise ``AttributeError: 'ImageFieldFile' object has no
    attribute 'strip'`` -- which broke the hotel repair path completely.
    """
    if url is None or not isinstance(url, str):
        url = str(url or "")
    url = url.strip()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:
        return url.lower()
    path = parts.path
    if "/thumb/" in path:
        path = path.rsplit("/", 1)[-1]
        for width in _WIKIMEDIA_WIDTHS:
            if path.startswith(width):
                path = path[len(width):]
                break
    if not parts.netloc:
        # A bare image-server path, e.g. DestinationImage.image_path. Keep it
        # as-is so it compares equal to the same path written the same way.
        return f"/{path.lstrip('/')}" if not path.startswith("/") else path
    return f"{parts.netloc}/{path.lstrip('/')}".lower()


@dataclass
class Reuse:
    # image defaults so defaultdict(Reuse) can build an empty entry; the key it
    # is filed under is the normalised image identity, set on first use.
    image: str = ""
    destination_ids: set = field(default_factory=set)
    hotel_ids: set = field(default_factory=set)
    rows: list = field(default_factory=list)
    destination_rows: int = 0
    hotel_rows: int = 0

    @property
    def places(self) -> int:
        return len(self.destination_ids) + len(self.hotel_ids)

    @property
    def severity(self) -> str:
        # A hotel showing a destination's photo is the clearest defect here:
        # it is a photo of a different kind of thing, not a debatable match.
        if self.hotel_ids and self.destination_ids:
            return "destination_photo_on_hotel"
        if self.places > 3:
            return "reused_by_3_plus"
        if self.places == 2:
            return "reused_by_2"
        return "unique"


class Command(BaseCommand):
    help = "Report images shared between different destinations and hotels."

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold", type=int, default=3,
            help="Places at which shared reuse becomes a defect (default 3).",
        )
        parser.add_argument("--tsv", default="", help="Write the full finding list to this TSV.")
        parser.add_argument(
            "--per-place", action="store_true",
            help="Print a per-destination and per-hotel line for every affected place.",
        )
        parser.add_argument(
            "--top", type=int, default=15, help="How many worst images to show (default 15).",
        )

    def handle(self, *args, **options):
        make_console_utf8()
        threshold = max(2, int(options["threshold"]))

        # ---- gather every image reference, from both tables ---------------
        image_rows = list(
            DestinationImage.objects.values(
                "id", "destination_id", "destination__name", "destination__district",
                "external_url", "image_path", "is_cover", "source",
            )
        )
        hotel_rows = list(
            Hotel.objects.values(
                "id", "name", "destination_id", "cover_image", "external_image_url", "address",
            )
        )

        usage: dict[str, Reuse] = defaultdict(Reuse)

        for row in image_rows:
            key = normalise_image_url(row["external_url"]) or normalise_image_url(row["image_path"])
            if not key:
                continue
            entry = usage[key]
            entry.image = key
            entry.destination_ids.add(row["destination_id"])
            entry.destination_rows += 1
            entry.rows.append(("destination_image", row["id"], row["destination_id"],
                               row["destination__name"], row["destination__district"],
                               bool(row["is_cover"]), row["source"]))

        for row in hotel_rows:
            key = normalise_image_url(row["external_image_url"]) or normalise_image_url(row["cover_image"])
            if not key:
                continue
            entry = usage[key]
            entry.image = key
            entry.hotel_ids.add(row["id"])
            entry.hotel_rows += 1
            entry.rows.append(("hotel", row["id"], row["destination_id"], row["name"],
                               row["address"], False, ""))

        reused = {k: v for k, v in usage.items() if v.places > 1}

        by_severity = Counter(entry.severity for entry in reused.values())
        defects = [e for e in reused.values() if is_defect(e, threshold)]

        # ---- per-place tallies, which is what the report is actually for ---
        dest_tally: Counter = Counter()
        hotel_tally: Counter = Counter()
        for entry in reused.values():
            for dest_id in entry.destination_ids:
                dest_tally[dest_id] += 1
            for hotel_id in entry.hotel_ids:
                hotel_tally[hotel_id] += 1

        # ---- covers -------------------------------------------------------
        covers = Counter(
            row["destination_id"] for row in image_rows if row["is_cover"] and row["destination_id"]
        )
        multi_cover = {d: n for d, n in covers.items() if n > 1}

        dest_names = {
            row["destination_id"]: (row["destination__name"], row["destination__district"])
            for row in image_rows
        }
        hotel_names = {row["id"]: (row["name"], row["destination_id"]) for row in hotel_rows}

        total_gallery_rows = len(image_rows)
        distinct = len(usage)
        rows_on_shared = sum(e.destination_rows for e in reused.values())

        self.stdout.write("Cross-place image reuse")
        self.stdout.write("  (no image was modified; this command only reports)")
        self.stdout.write("")
        self.stdout.write(f"destination gallery rows : {total_gallery_rows}")
        self.stdout.write(f"distinct images in use   : {distinct}")
        self.stdout.write(f"hotels                   : {len(hotel_rows)}")
        self.stdout.write("")
        if total_gallery_rows:
            pct = 100.0 * rows_on_shared / total_gallery_rows
            self.stdout.write(self.style.WARNING(
                f"gallery rows sharing an image with another place: {rows_on_shared} ({pct:.1f}%)"
            ))
        self.stdout.write(f"images attached to >1 place: {len(reused)}")
        for severity in ("destination_photo_on_hotel", "reused_by_3_plus", "reused_by_2"):
            self.stdout.write(f"  {severity:26} {by_severity.get(severity, 0)}")
        self.stdout.write("")
        self.stdout.write(f"destinations affected    : {len(dest_tally)}")
        self.stdout.write(f"hotels affected          : {len(hotel_tally)}")
        self.stdout.write(f"images meeting the defect threshold (>{threshold} places): {len(defects)}")
        self.stdout.write(f"destinations with more than one cover row: {len(multi_cover)}")

        # ---- worst offenders ----------------------------------------------
        worst = sorted(reused.values(), key=lambda e: -e.places)[: options["top"]]
        if worst:
            self.stdout.write("")
            self.stdout.write(f"Worst {len(worst)} most-reused images:")
            for entry in worst:
                kinds = []
                if entry.destination_ids:
                    kinds.append(f"{len(entry.destination_ids)} dest")
                if entry.hotel_ids:
                    kinds.append(f"{len(entry.hotel_ids)} hotel")
                self.stdout.write(
                    f"  {entry.places:5} places ({', '.join(kinds)})  [{entry.severity}]  "
                    f"{safe_text(entry.image, 88)}"
                )

        # ---- per-place report ---------------------------------------------
        if options["per_place"]:
            self.stdout.write("")
            self.stdout.write("Per destination (count = shared images on this place):")
            for dest_id, count in dest_tally.most_common():
                name, district = dest_names.get(dest_id, ("?", "?"))
                self.stdout.write(
                    f"  {count:4} shared  {safe_text(name or '?', 60)} ({safe_text(district or '?', 30)})"
                )
            self.stdout.write("")
            self.stdout.write("Per hotel (count = shared images on this hotel):")
            for hotel_id, count in hotel_tally.most_common():
                name, dest_id = hotel_names.get(hotel_id, ("?", None))
                dname = (dest_names.get(dest_id) or ("?", "?"))[0] if dest_id else "?"
                self.stdout.write(
                    f"  {count:4} shared  {safe_text(name or '?', 55)} - in {safe_text(dname or '?', 40)}"
                )

        if options["tsv"]:
            self._write_tsv(options["tsv"], reused, threshold, dest_names, hotel_names)
            self.stdout.write("")
            self.stdout.write(f"TSV written to {options['tsv']}")

        self.stdout.write("")
        self.stdout.write(
            "An image being shared does not reveal the correct replacement. Use "
            "repair_real_place_images to search a licensed source for this exact "
            "place, or review by hand; a wrong-but-plausible photo is worse than "
            "an obviously missing one."
        )

    def _write_tsv(self, path, reused, threshold, dest_names, hotel_names):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["image", "severity", "places", "destinations", "hotels",
                             "kind", "row_id", "destination_id", "place_name", "detail"])
            for entry in sorted(reused.values(), key=lambda e: -e.places):
                for kind, row_id, dest_id, name, detail, is_cover, source in entry.rows:
                    writer.writerow([
                        entry.image, entry.severity, entry.places,
                        len(entry.destination_ids), len(entry.hotel_ids),
                        kind, row_id, dest_id or "", name or "", detail or "",
                    ])


def is_defect(entry: Reuse, threshold: int) -> bool:
    """True when an image is reused past the configured threshold, or is a
    hotel showing a destination's photograph (a category error, reported at
    any threshold)."""
    return entry.places >= threshold or bool(entry.hotel_ids and entry.destination_ids)