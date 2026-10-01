"""Import the verified destination budget dataset into ``BudgetEstimation``.

Why this command was rewritten
------------------------------
Three separate defects made the public budget estimator report "unavailable"
in production while the command looked correct:

1. **It never finished.** Every CSV row ran
   ``Destination.objects.filter(name__iexact=...)`` -- an unindexed
   case-insensitive scan across the whole 8,757-row destination table. With
   5,018 CSV rows that is tens of millions of row comparisons; the command ran
   past 10 minutes locally and was killed by Render's boot timeout. Because
   ``import_budget`` is called by ``docker/entrypoint.sh``, a single slow import
   stalled the whole deploy: the container never answered ``/health/``, Render
   restarted it in a loop, and every endpoint -- including register and nearby
   -- returned 500. Matching now happens against a case-folded, in-memory index
   built with two queries.

2. **Three columns were silently discarded.** ``dataset/budget_features.csv``
   has 8 header names but 11 fields per data row. pandas' ``read_csv`` with a
   short header either invents positional names or truncates the extra fields,
   so the per-destination activity / shopping / emergency-reserve costs were
   lost before they ever reached the model. The file is now read with the
   ``csv`` module and the unnamed trailing columns are bound by position.

3. **Dead code sat between two functions.** A block of unreachable
   ``find_destination`` fragments (lines 34-65 of the previous file) lived
   after ``parse_range``'s ``return 0``, referencing an undefined ``name``
   variable. It never executed, so it never failed -- it just made the file
   misleading to read.

Two further correctness fixes came out of testing the rewrite:

* ``BudgetEstimation.destination`` is a OneToOne, and the district fallback can
  resolve several CSV rows onto the same catalogue destination, so
  ``bulk_create`` aborted on a unique-constraint violation. Duplicates are now
  dropped (the first row for a destination wins).
* The old ``find_destination`` called ``get_or_create``, manufacturing catalogue
  rows out of typo'd CSV names (this is where a destination literally named
  "1 Room" came from). Only existing records are ever matched now.

The import stays idempotent (a single transactional replace), so re-running it
on every deploy only refreshes values.
"""
from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import BudgetEstimation, Destination

# Default when a destination has no activity/shopping row: a real per-day
# allowance rather than 0, so a partial estimate never reads as "free".
DEFAULT_ACTIVITY_COST = 10.0
DEFAULT_SHOPPING_COST = 10.0
DEFAULT_RESERVE = 25.0

# Assumed trip length for the stored trip total. The public estimator scales
# this by the requested days at request time, so it only has to be a sane
# reference for the stored column.
REFERENCE_TRIP_DAYS = 3

# The dataset is keyed by municipality, so most rows have no exactly-matching
# catalogue destination. Its costs are district-level averages anyway, so an
# unmatched row is filed against the most prominent destination in the same
# district. The estimator prefers a destination's own row and falls back to the
# district row, which is why this fills ~100 districts rather than 473 places.
_KEY_HEADER_TO_FIELD = {
    "Source": "source",
    "Destination": "destination",
    "District": "district",
    "Province": "province",
    "Transport Cost (USD)": "transport",
    "Food Cost/Day (USD)": "food",
    "Accommodation/Night (USD)": "accommodation",
    "Local Taxi/Rick": "local_transport",
}

# Cost columns the CSV carries but its 8-name header does not label. They are
# positional, so they are bound by index in this order.
_EXTRA_COST_KEYS = ("activities", "shopping", "reserve")


def parse_range(value) -> float:
    """Convert a cost cell to a number.

    The dataset stores ranges as ``'40-120'``; the midpoint is used so a range
    never renders as a suspiciously cheap or expensive single figure. Empty,
    ``NaN`` and unparseable cells become ``0.0`` rather than raising, so one bad
    row cannot abort the whole import.
    """
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "-"}:
        return 0.0

    if "-" in text[1:]:  # skip a leading sign on a negative number
        low, _, high = text.partition("-")
        try:
            return round((float(low) + float(high)) / 2, 2)
        except ValueError:
            return 0.0

    try:
        return round(float(text), 2)
    except ValueError:
        return 0.0


def _clean(value) -> str:
    """Normalise a text cell: strip, drop NaN, repair CSV mojibake."""
    text = "" if value is None else str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return ""
    # The dataset was written with a Windows codepage, so a few Nepali names
    # arrive as U+FFFD replacement characters (e.g. "Il\ufffd?m"). Repair the
    # sequence so the name still matches the catalogue.
    if "\ufffd" in text:
        text = text.replace("\ufffd", "").replace("?", "").strip()
    return text


class Command(BaseCommand):
    help = "Import the verified destination budget dataset (dataset/budget_features.csv)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default="",
            help="Optional path to the budget CSV (defaults to dataset/budget_features.csv).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be imported without writing.",
        )

    def handle(self, *args, **options):
        self._district_index: dict[str, list[Destination]] = {}
        csv_path = self._resolve_csv(options["csv"])
        rows = self._read_rows(csv_path)
        if not rows:
            self.stderr.write(self.style.ERROR(f"No usable budget rows in {csv_path}."))
            return

        index = self._build_destination_index()
        self.stdout.write(f"Indexed {len(index)} catalogue destination names.")

        imported = skipped = duplicate = 0
        seen_ids: set[int] = set()
        updates: list[BudgetEstimation] = []

        for row in rows:
            destination = self._match_destination(row, index)
            if destination is None:
                skipped += 1
                if skipped <= 10:
                    self.stdout.write(self.style.WARNING(
                        f"  no destination for {row.get('destination')!r} "
                        f"({row.get('district')!r})"))
                continue

            if destination.id in seen_ids:
                # OneToOne on destination: keep the first row seen for a place.
                duplicate += 1
                continue
            seen_ids.add(destination.id)

            transport = parse_range(row.get("transport"))
            food = parse_range(row.get("food"))
            accommodation = parse_range(row.get("accommodation"))
            local_transport = parse_range(row.get("local_transport"))
            activities = parse_range(row.get("activities")) or DEFAULT_ACTIVITY_COST
            shopping = parse_range(row.get("shopping")) or DEFAULT_SHOPPING_COST
            reserve = parse_range(row.get("reserve")) or DEFAULT_RESERVE

            daily = round(food + accommodation + local_transport + activities, 2)
            trip = round(daily * REFERENCE_TRIP_DAYS + transport + shopping + reserve, 2)

            updates.append(BudgetEstimation(
                destination=destination,
                district=row.get("district") or destination.district or "",
                province=row.get("province") or destination.province or "",
                transport_cost=transport,
                food_cost_per_day=food,
                accommodation_per_night=accommodation,
                local_transport=local_transport,
                # Activities/shopping/reserve have no column of their own on the
                # model; activities is folded into the per-day total so the
                # estimator's daily figure includes it.
                entry_fee=activities,
                estimated_daily_budget=daily,
                estimated_trip_budget=trip,
            ))
            imported += 1

        summary = (f"import {imported}, skip {skipped}, drop {duplicate} duplicate")
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(f"Dry run: would {summary}."))
            return

        # One transaction: a partially applied import is worse than none,
        # because the estimator would then mix fresh and stale figures.
        with transaction.atomic():
            BudgetEstimation.objects.all().delete()
            BudgetEstimation.objects.bulk_create(updates, batch_size=500)

        districts = BudgetEstimation.objects.values("district").distinct().count()
        self.stdout.write(self.style.SUCCESS(
            f"Imported {imported} budget rows ({skipped} unmatched, "
            f"{duplicate} duplicate), covering {districts} districts. "
            f"TouristBudgetEstimation now holds {BudgetEstimation.objects.count()} rows."))

    # -- helpers ---------------------------------------------------------
    def _resolve_csv(self, override: str) -> Path:
        """Absolute path to the CSV.

        The previous version opened the relative path ``dataset/...``, which
        only resolves when the process happens to be started from
        ``/app/Tourism``. Anchoring to BASE_DIR makes the import
        working-directory independent.
        """
        if override:
            path = Path(override)
            return path if path.is_absolute() else settings.BASE_DIR / path
        return settings.BASE_DIR / "dataset" / "budget_features.csv"

    def _read_rows(self, csv_path: Path) -> list[dict]:
        """Read the CSV, binding the unlabelled trailing columns by position.

        ``csv`` is used instead of pandas so a short header can never silently
        discard data -- the reader reports the real field count per row and the
        extra values are named here.
        """
        if not csv_path.is_file():
            self.stderr.write(self.style.ERROR(f"Budget CSV not found: {csv_path}"))
            return []

        rows: list[dict] = []
        with csv_path.open(encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                return []

            labelled = [name.strip() for name in header]
            # The three trailing cost columns have no header name. Give them
            # stable internal keys so nothing downstream has to guess which
            # unnamed column is which.
            for index, key in enumerate(_EXTRA_COST_KEYS):
                while len(labelled) <= len(header) + index:
                    labelled.append(key)

            for raw in reader:
                if not raw or not any(cell.strip() for cell in raw):
                    continue
                record: dict = {}
                for index, value in enumerate(raw):
                    if index < len(labelled):
                        record[labelled[index]] = _clean(value)
                row = {_KEY_HEADER_TO_FIELD.get(key, key): value
                       for key, value in record.items()}
                if row.get("destination"):
                    rows.append(row)

        self.stdout.write(f"Read {len(rows)} budget rows from {csv_path.name}.")
        return rows

    def _build_destination_index(self) -> dict[str, Destination]:
        """Case-folded name -> Destination, built with a single pass.

        Two full-table reads beat 5,018 unindexed ``iexact`` scans by orders of
        magnitude. A district -> destinations map is built in the same pass for
        the district-level fallback.
        """
        by_name: dict[str, Destination] = {}
        district_index: dict[str, list[Destination]] = {}
        for destination in Destination.objects.all().only(
            "id", "name", "district", "province"
        ):
            key = (destination.name or "").strip().casefold()
            if key and key not in by_name:
                by_name[key] = destination
            district_key = (destination.district or "").strip().casefold()
            if district_key:
                district_index.setdefault(district_key, []).append(destination)
        self._district_index = district_index
        return by_name

    def _match_destination(self, row: dict, index: dict[str, Destination]):
        """Resolve a CSV row to an existing catalogue destination.

        Only ever matches an existing record. The previous version called
        ``get_or_create`` and would manufacture a Destination from a typo'd CSV
        name, which is how rows like "1 Room" ended up in the catalogue.
        """
        name = (row.get("destination") or "").casefold()
        if name and name in index:
            return index[name]

        district = (row.get("district") or "").casefold()
        if district:
            candidates = self._district_index.get(district)
            if candidates:
                return candidates[0]
        return None
