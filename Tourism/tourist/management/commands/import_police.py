"""Import police stations from the tracked CSV into ``PoliceStation``.

Why this command was rewritten
------------------------------
It took **741 seconds** and exited non-zero, and it ran on the Render boot
path, so it was one of the reasons the container never answered its health
check.

Two separate defects:

1. **It never finished.** ``find_destination`` evaluated its coordinate fallback
   by pulling the *entire* destination catalogue out of the database and
   computing a haversine distance in Python -- once per CSV row. With 2,601
   rows against 8,757 destinations that is ~23 million distance calculations
   plus 2,601 full table reads. Matching now goes through
   ``tourist.destination_matching.DestinationMatcher``, which builds the name
   and coordinate indexes once with two queries and answers from memory.

2. **It crashed.** The coordinate fallback selected candidates with
   ``Destination.objects.exclude(latitude__isnull=True, longitude__isnull=True)``.
   In Django, ``exclude()`` with several keyword arguments means "NOT (all of
   these are true)", i.e. *not both null* -- so it returned exactly the rows
   that should have been excluded, including destinations with a null
   coordinate. ``float(None)`` then raised ``TypeError`` and the import aborted
   part-way with a non-zero exit, leaving the table half-populated.

Also fixed: the CSV path is resolved against ``BASE_DIR`` instead of the
current working directory, and the header is read with the ``csv`` module so a
short header cannot silently drop columns (the cleaned file carries
``data_quality_score``, which pandas mangled into positional column names).
"""
from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from tourist.destination_matching import DestinationMatcher
from tourist.models import PoliceStation

# How far a CSV row may sit from the destination it is filed under. The
# original code used 20 km for its coordinate fallback; kept identical so the
# resulting data set is unchanged, only fast.
MATCH_RADIUS_KM = 20.0

# Preferred file, then fallbacks, so the entrypoint's explicit
# --csv dataset/nearbypolice.csv and a bare `import_police` both work.
CSV_CANDIDATES = (
    "dataset/police_station_cleaned.csv",
    "dataset/nearbypolice.csv",
    "dataset/police.csv",
)

_COLUMN_ALIASES = {
    "name": "police_station",
    "station": "police_station",
    "station_name": "police_station",
    "destination": "destination",
    "place": "destination",
    "address": "address",
    "phone": "phone",
    "phone_number": "phone",
    "contact": "phone",
    "lat": "latitude",
    "latitude": "latitude",
    "lng": "longitude",
    "lon": "longitude",
    "longitude": "longitude",
    "district": "district",
    "province": "province",
}


def _text(value) -> str:
    """Normalise a cell to a clean string, dropping pandas/CSV filler."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return ""
    return text


def _coordinate(value):
    """Parse a coordinate cell, returning ``None`` when it is not a number."""
    text = _text(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    # 0/0 is the dataset's "unknown", not a real position in Nepal.
    return None if (number == 0.0) else number


class Command(BaseCommand):
    help = "Import police stations from CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default="",
            help="CSV path (defaults to the first existing of "
                 + ", ".join(CSV_CANDIDATES) + ").",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be imported without writing.",
        )

    def handle(self, *args, **options):
        csv_path = self._resolve_csv(options.get("csv"))
        if csv_path is None:
            self.stderr.write(self.style.ERROR("No police station CSV found."))
            return

        rows = self._read_rows(csv_path)
        # Both coordinates are non-null columns on the model, so a row without
        # a usable pair cannot be stored at all. The raw nearbypolice.csv
        # repeats its header mid-file, and this is also what dropped those
        # rows before.
        usable = [
            row for row in rows
            if row["latitude"] is not None and row["longitude"] is not None
        ]
        self.stdout.write(
            f"Read {len(rows)} rows from {csv_path.name} "
            f"({len(rows) - len(usable)} without usable coordinates)."
        )
        if not usable:
            return

        matcher = DestinationMatcher()
        self.stdout.write(
            f"Indexed {len(matcher)} destination names "
            f"({matcher.located_count} with usable coordinates)."
        )

        imported = skipped = 0
        unmatched: list[str] = []

        for row in usable:
            destination = matcher.match(
                name=row["destination"],
                district=row["district"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                max_km=MATCH_RADIUS_KM,
            )
            if destination is None:
                skipped += 1
                if len(unmatched) < 10:
                    unmatched.append(f"{row['name'] or '(unnamed)'} ({row['destination'] or 'no destination'})")
                continue

            # destination is a ForeignKey, so a place can legitimately have
            # several stations; the (destination, name) pair is the identity.
            PoliceStation.objects.update_or_create(
                destination=destination,
                name=row["name"] or f"Police station ({destination.name})",
                defaults={
                    "address": row["address"] or destination.name or "Nepal",
                    "phone": row["phone"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "coordinate_source": "dataset_csv",
                    "coordinate_status": "recorded",
                },
            )
            imported += 1

        for line in unmatched:
            self.stdout.write(self.style.WARNING(f"  no destination for {line}"))

        self.stdout.write(self.style.SUCCESS(
            f"Imported {imported} police stations, skipped {skipped}. "
            f"PoliceStation now holds {PoliceStation.objects.count()} rows."))

    # -- helpers ---------------------------------------------------------
    def _resolve_csv(self, override: str) -> Path | None:
        """Absolute path to the CSV, working-directory independent."""
        if override:
            path = Path(override)
            if not path.is_absolute():
                path = settings.BASE_DIR / path
            return path if path.is_file() else None
        for relative in CSV_CANDIDATES:
            candidate = settings.BASE_DIR / relative
            if candidate.is_file():
                return candidate
        return None

    def _read_rows(self, csv_path: Path) -> list[dict]:
        """Read the CSV, mapping the known header spellings to fixed keys."""
        rows: list[dict] = []
        with csv_path.open(encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return []
            # Map the file's own column names onto the keys used below, so
            # `raw.get(column)` reads the real header. Keys are original
            # header -> internal key; normalising the *lookup* name instead of
            # the *read* name silently yields None for every cell.
            mapping: dict[str, str] = {}
            for header in reader.fieldnames or []:
                normalised = (header or "").strip().lower().replace(" ", "_")
                mapping[header] = _COLUMN_ALIASES.get(normalised, normalised)

            for raw in reader:
                row = {
                    key: _text(raw.get(header))
                    for header, key in mapping.items()
                }
                if not any(row.values()):
                    continue
                rows.append({
                    "name": row.get("police_station", ""),
                    "destination": row.get("destination", ""),
                    "district": row.get("district", ""),
                    "address": row.get("address", ""),
                    "phone": row.get("phone", ""),
                    "latitude": _coordinate(row.get("latitude")),
                    "longitude": _coordinate(row.get("longitude")),
                })
        return rows
