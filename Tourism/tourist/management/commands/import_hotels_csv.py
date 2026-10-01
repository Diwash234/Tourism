"""
Offline import of hotels from Tourism/dataset/hotel.csv.

The existing import_hotels command relies on live reverse-geocoding
(Nominatim), which is slow and fails without network. This command reads
the CSV directly, matches each hotel to a Destination by city/destination
name, and assigns a relevant cover image via the photo catalog. It is safe
to re-run: existing hotels (matched by name) are skipped.

Usage:
    python manage.py import_hotels_csv
    python manage.py import_hotels_csv --csv /path/to/hotel.csv

Why the lookup is indexed
-------------------------
Matching used to issue up to six unindexed queries *per CSV row*: an
``Hotel.objects.filter(name__iexact=...)`` existence check, four
``Destination`` ``iexact`` lookups, and one four-field ``icontains`` ``Q``
query. Across 2,105 rows that is ~12,000 case-insensitive full-table scans
over the 8,757-row destination catalogue, and the command took 313 seconds.
It runs on the Render boot path, so that is minutes of container start-up
before Daphne can bind its port.

The matching rules are unchanged. The candidate maps and the existing-hotel
name set are now built once with two queries and every row is answered from
memory. The resolution is additionally memoised per city string, because all
hotels in one city resolve to the same destination.
"""
import csv
import os
import re
import unicodedata

from django.core.management.base import BaseCommand

from tourist.models import Hotel, Destination
from tourist import photo_catalog


def _norm(value) -> str:
    """Fold a place name to a comparable ASCII key."""
    value = unicodedata.normalize(
        "NFKD", str(value or "")
    ).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


class _DestinationIndex:
    """In-memory stand-in for the per-row Destination lookups.

    Maps are filled in default queryset order, so the first entry stored for a
    key is exactly the row ``.first()`` used to return.
    """

    def __init__(self):
        self.by_city: dict[str, Destination] = {}
        self.by_district: dict[str, Destination] = {}
        self.by_province: dict[str, Destination] = {}
        self.by_name: dict[str, Destination] = {}
        # (id, haystack, destination) in id order for the icontains fallback.
        self.fuzzy: list[tuple[int, str, Destination]] = []
        # Per-city memo: hotels in one city all resolve identically.
        self._memo: dict[str, Destination | None] = {}

        for destination in Destination.objects.all().only(
            "id", "name", "city", "district", "province"
        ):
            parts = [
                _norm(destination.city),
                _norm(destination.district),
                _norm(destination.province),
                _norm(destination.name),
            ]
            for mapping, key in zip(
                (self.by_city, self.by_district, self.by_province, self.by_name),
                parts,
            ):
                if key and key not in mapping:
                    mapping[key] = destination
            self.fuzzy.append(
                (destination.id, " ".join(p for p in parts if p), destination)
            )

    def resolve(self, city: str):
        if not city:
            return None
        if city in self._memo:
            return self._memo[city]

        key = _norm(city)
        tokens = [t for t in key.split() if t not in {"region", "province", "area"}]
        candidates = [key, " ".join(tokens)] if tokens else [key]

        found = None
        for candidate in dict.fromkeys(candidates):
            if not candidate:
                continue
            found = (
                self.by_city.get(candidate)
                or self.by_district.get(candidate)
                or self.by_province.get(candidate)
                or self.by_name.get(candidate)
            )
            if found:
                break

        if found is None:
            # Mirrors the old `Q(field__icontains=token) ... .order_by("id")`
            # fallback, but without a query per row.
            wanted = [t for t in tokens if len(t) >= 3]
            if wanted:
                for _id, haystack, destination in self.fuzzy:
                    if any(token in haystack for token in wanted):
                        found = destination
                        break

        self._memo[city] = found
        return found


class Command(BaseCommand):
    help = "Import hotels from hotel.csv (offline, no geocoding)."

    def add_arguments(self, parser):
        default = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "dataset", "hotel.csv"))
        parser.add_argument("--csv", default=default)

    def handle(self, *args, **options):
        path = options["csv"]
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"CSV not found: {path}"))
            return

        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.stdout.write(f"Loaded {len(rows)} hotels from {os.path.basename(path)}")

        index = _DestinationIndex()
        # One query for "which hotels already exist" instead of one per row.
        existing = {
            name.casefold()
            for name in Hotel.objects.values_list("name", flat=True)
        }
        self.stdout.write(
            f"Indexed {len(index.by_name)} destination names and "
            f"{len(existing)} existing hotels"
        )

        created = 0
        skipped = 0
        for i, row in enumerate(rows, 1):
            name = (row.get("Hotel Name") or "").strip()
            if not name:
                continue
            if name.casefold() in existing:
                skipped += 1
                continue

            city = (row.get("Destination") or "").strip()
            dest = index.resolve(city)
            if dest is None:
                # Never attach an unrelated hotel to the first destination in
                # the database. That creates the exact cross-place pollution
                # seen on production destination pages.
                skipped += 1
                if skipped <= 10:
                    self.stdout.write(self.style.WARNING(
                        f"Hotel destination not matched; skipped: {name} ({city})"
                    ))
                continue

            try:
                lat = float(row.get("Latitude")) if row.get("Latitude") else None
                lon = float(row.get("Longitude")) if row.get("Longitude") else None
            except (TypeError, ValueError):
                lat = lon = None

            try:
                rating = float(row.get("Rating")) if row.get("Rating") else None
            except (TypeError, ValueError):
                rating = None
            try:
                price = float(row.get("Price Per Night")) if row.get("Price Per Night") else None
            except (TypeError, ValueError):
                price = None

            photo = photo_catalog.resolve_hotel_photo(
                type("H", (), {"name": name, "id": i})()
            )

            status_map = {
                "available": "available",
                "booked": "booked",
                "closed": "closed",
            }
            booking_status = status_map.get(
                (row.get("Booking Status") or "").strip().lower(), "unknown"
            )

            Hotel.objects.create(
                destination=dest,
                name=name[:200],
                address=(row.get("Address") or "")[:255],
                latitude=lat,
                longitude=lon,
                rating=rating,
                price_per_night=price,
                currency=(row.get("Currency") or "USD")[:10],
                booking_status=booking_status,
                booking_url=(row.get("Booking URL") or "")[:500],
                external_image_url=photo["url"],
                cover_image=photo["url"],
                source="dataset",
            )
            # Keep the in-memory set current so a duplicated CSV row is not
            # inserted twice within the same run.
            existing.add(name.casefold())
            created += 1
            if i % 250 == 0:
                self.stdout.write(f"  [{i}/{len(rows)}] created={created} skipped={skipped}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. created={created} skipped={skipped} total_hotels={Hotel.objects.count()}"
        ))
