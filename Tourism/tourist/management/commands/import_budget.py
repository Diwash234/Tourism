"""Import recorded travel-cost baselines from dataset/budget_features.csv.

Why this was rewritten
----------------------
The previous matcher was, in order:

    1. exact name match
    2. ``Destination.objects.filter(district=...).first()``   <-- the bug
    3. create a new destination

Step 2 attached a CSV row to an *arbitrary* destination in the same district.
Because ``BudgetEstimation.destination`` is a OneToOneField, every later row for
that district overwrote the previous one, so 5,018 source rows collapsed onto
546 destinations -- and 51 of those rows ended up describing a place in a
completely different district from the one they were recorded for (a Solukhumbu
budget on a Ramechhap destination, a Koshi Tappu budget on a Saptari/Morang
one). That is fabricated data presented as this place's recorded cost.

Matching is now strictly tiered and never guesses. Anything that cannot be
matched confidently is reported as unmatched and left out; those destinations
are still served a real figure by ``budget_baseline.recorded_budget_baseline``,
which falls back to the district and then province median and labels which one
it used.
"""

import csv
import os
import re
import unicodedata

from django.core.management.base import BaseCommand

from tourist.models import BudgetEstimation, Destination

DEFAULT_CSV = os.path.join("dataset", "budget_features.csv")

COL_SOURCE = "Source"
COL_DESTINATION = "Destination"
COL_DISTRICT = "District"
COL_PROVINCE = "Province"
COL_TRANSPORT = "Transport Cost (USD)"
COL_FOOD = "Food Cost/Day (USD)"
COL_ACCOMMODATION = "Accommodation/Night (USD)"
COL_LOCAL = "Local Taxi/Rick"


def parse_range(value):
    """'40-120' -> 80.0 (midpoint), '20' -> 20.0, blank/garbage -> 0.0.

    The source dataset records ranges, not prices, so the midpoint is used and
    the response tells the caller it is a recorded baseline rather than a quote.
    """
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "-"}:
        return 0.0
    if "-" in text:
        parts = [p for p in re.split(r"[-–—]", text) if p.strip()]
        if len(parts) == 2:
            try:
                return (float(parts[0]) + float(parts[1])) / 2.0
            except ValueError:
                return 0.0
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return 0.0


def normalise(text):
    """Lowercase, strip accents and collapse punctuation for tolerant matching."""
    if text is None:
        return ""
    folded = unicodedata.normalize("NFKD", str(text))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    folded = re.sub(r"[^a-z0-9]+", " ", folded.lower())
    return " ".join(folded.split())


class Command(BaseCommand):
    help = "Import recorded travel-cost baselines from budget_features.csv"

    def add_arguments(self, parser):
        parser.add_argument("--file", default=DEFAULT_CSV)
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report what would be imported without writing.",
        )
        parser.add_argument(
            "--prune-mismatched", action="store_true",
            help="Delete existing rows whose recorded district disagrees with the "
                 "destination they were attached to (provably mis-attributed).",
        )
        parser.add_argument("--report", type=int, default=20,
                            help="How many unmatched source rows to print.")

    # -- matching ---------------------------------------------------------
    def _index_destinations(self):
        """name/slug -> row dict, built once.

        Holding the pk here matters: resolving each matched row with a fresh
        ``Destination.objects.filter(name=...)`` meant ~2,200 full-table scans
        on an unindexed name column, and the import did not finish in ten
        minutes.
        """
        by_name, by_slug = {}, {}
        for pk, name, slug, district, province in Destination.objects.values_list(
            "id", "name", "slug", "district", "province"
        ):
            row = {"pk": pk, "name": name, "district": district, "province": province}
            key = normalise(name)
            if key and key not in by_name:
                by_name[key] = row
            if slug:
                by_slug.setdefault(normalise(slug), row)
        return by_name, by_slug

    def _prefix_index(self, by_name):
        """first word -> rows, so the prefix tier stays a dict lookup."""
        index = {}
        for key, row in by_name.items():
            index.setdefault(key.split(" ", 1)[0], []).append((key, row))
        return index

    def _match_prefix(self, key, prefix_index):
        """Match "<place>" to "<place> <qualifier>" only when it is unambiguous.

        The source labels a town as "Nagarkot" while the catalogue calls it
        "Nagarkot-Dhulikhel Mountain Biking". Accepting a prefix would recover
        those rows, but only when exactly ONE destination starts that way --
        otherwise "Manang" or "Tansen" would silently pick a random place in a
        district with several candidates, which is the exact mistake this
        rewrite exists to remove.
        """
        candidates = prefix_index.get(key.split(" ", 1)[0], [])
        matches = [
            row for full, row in candidates
            if full.startswith(key + " ") or key.startswith(full + " ")
        ]
        if len(matches) == 1:
            return matches[0], "prefix"
        return None, None

    def _match(self, raw_name, district, by_name, by_slug):
        """Return (row_dict, tier) or (None, None). Never guesses.

        Tiers, most to least confident:
          exact      - the place name matches a destination exactly
          slug       - the place name matches a destination slug
          district   - "<district> <place>" or "<place> <district>" collapsed
                       into one string, which is how the source labels towns
        """
        key = normalise(raw_name)
        if not key:
            return None, None

        if key in by_name:
            return by_name[key], "exact"
        if key in by_slug:
            return by_slug[key], "slug"

        district_key = normalise(district)
        if district_key:
            if key.endswith(" " + district_key):
                return self._lookup(key[: -len(district_key) - 1].strip(), by_name, by_slug)
            if key.startswith(district_key + " "):
                return self._lookup(key[len(district_key) + 1:].strip(), by_name, by_slug)
        return None, None

    @staticmethod
    def _lookup(key, by_name, by_slug):
        if key in by_name:
            return by_name[key], "district"
        if key in by_slug:
            return by_slug[key], "district"
        return None, None

    # -- pruning ----------------------------------------------------------
    def _prune(self):
        removed = []
        for row in BudgetEstimation.objects.select_related("destination").all():
            row_district = normalise(row.district)
            dest_district = normalise(getattr(row.destination, "district", "") or "")
            # Only prune when both sides actually recorded a district, so a
            # missing value is never treated as a contradiction.
            if row_district and dest_district and row_district != dest_district:
                removed.append((row.destination.name, row.district, row.destination.district))
                row.delete()
        return removed

    # -- main -------------------------------------------------------------
    def handle(self, *args, **options):
        path = options["file"]
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"Dataset not found: {path}"))
            return

        if options["prune_mismatched"]:
            removed = self._prune()
            self.stdout.write(self.style.WARNING(
                f"Pruned {len(removed)} mis-attached budget row(s)"
            ))
            for name, row_district, dest_district in removed[:options["report"]]:
                self.stdout.write(f"   {name}: row says {row_district}, place is in {dest_district}")
            if options["dry_run"]:
                return

        with open(path, encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.stdout.write(f"Source rows: {len(rows)}")

        by_name, by_slug = self._index_destinations()
        prefix_index = self._prefix_index(by_name)
        self.stdout.write(f"Destinations indexed: {len(by_name)}")

        imported, tiers, unmatched = 0, {}, []
        for row in rows:
            destination_row, tier = self._match(
                row.get(COL_DESTINATION), row.get(COL_DISTRICT), by_name, by_slug
            )
            if destination_row is None:
                destination_row, tier = self._match_prefix(
                    normalise(row.get(COL_DESTINATION)), prefix_index
                )
            if destination_row is None:
                unmatched.append((row.get(COL_DESTINATION), row.get(COL_DISTRICT)))
                continue

            transport = parse_range(row.get(COL_TRANSPORT))
            food = parse_range(row.get(COL_FOOD))
            accommodation = parse_range(row.get(COL_ACCOMMODATION))
            local = parse_range(row.get(COL_LOCAL))
            daily = food + accommodation + local

            tiers[tier] = tiers.get(tier, 0) + 1
            if options["dry_run"]:
                imported += 1
                continue

            # The destination's own location wins over the source label:
            # recording the row's district here is what made the previous
            # import mis-attributable in the first place.
            district_name = destination_row["district"] or row.get(COL_DISTRICT, "") or ""
            province_name = destination_row["province"] or row.get(COL_PROVINCE, "") or ""

            BudgetEstimation.objects.update_or_create(
                destination_id=destination_row["pk"],
                defaults={
                    "district": district_name,
                    "province": province_name,
                    "transport_cost": transport,
                    "food_cost_per_day": food,
                    "accommodation_per_night": accommodation,
                    "local_transport": local,
                    "entry_fee": 0,
                    "estimated_daily_budget": daily,
                    "estimated_trip_budget": daily * 3,
                },
            )
            imported += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Matched and imported: {imported} / {len(rows)}"
        ))
        for tier, count in sorted(tiers.items()):
            self.stdout.write(f"   via {tier:<9} {count}")
        self.stdout.write(self.style.WARNING(
            f"Unmatched (left out, served by the district/province median): {len(unmatched)}"
        ))
        for name, district in unmatched[:options["report"]]:
            self.stdout.write(f"   {str(name)[:50]:<52} {district or ''}")

        total = BudgetEstimation.objects.count() if not options["dry_run"] else 0
        self.stdout.write("")
        self.stdout.write(f"BudgetEstimation rows now: {total}")
