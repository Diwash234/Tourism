"""Normalize destination district/province strings to the canonical tables.

The bundled OSM dataset stores ``district`` in Devanagari (often suffixed
"जिल्ला") and ``province`` in Nepali ("गण्डकी प्रदेश" etc.), while the rest of
the platform queries districts by their canonical English names from the
77-district table. Query-side aliases (see
``tourist.municipality_mappings.DISTRICT_ALIASES``) already make reads work;
this command cleans the stored data so every consumer — itineraries, filters,
analytics, admin — sees one canonical spelling.

Safe and idempotent: only rows whose district/province resolve to a *known*
canonical name are rewritten; anything unresolvable is left untouched and
reported (never guessed). The Devanagari locality is preserved in
``city_nepali`` by the importer, so no information is lost.

Usage:
    python manage.py normalize_district_names            # apply
    python manage.py normalize_district_names --dry-run  # report only
"""
import re

from django.core.management.base import BaseCommand

from tourist.models import Destination
from tourist.municipality_mappings import canonical_district, canonical_province

DEVANAGARI = re.compile(r"[\u0900-\u097F]")


class Command(BaseCommand):
    help = "Normalize destination district/province strings to canonical English names."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        changed = 0
        unresolved = {}
        qs = Destination.objects.exclude(district__isnull=True).exclude(district="")
        for d in qs.iterator():
            nd = canonical_district(d.district)
            np_ = canonical_province(d.province) if d.province else d.province
            if nd == d.district and (np_ or "") == (d.province or ""):
                continue
            if DEVANAGARI.search(nd):
                # Still Devanagari after canonicalization: unknown spelling.
                # Leave it as-is — we never guess.
                unresolved[nd] = unresolved.get(nd, 0) + 1
                continue
            if not dry:
                d.district, d.province = nd, np_
                d.save(update_fields=["district", "province"])
            changed += 1
        verb = "would normalize" if dry else "normalized"
        self.stdout.write(f"{verb.capitalize()} {changed} destination rows"
                          + (" (dry run)" if dry else ""))
        if unresolved:
            self.stdout.write("Unresolved district spellings left untouched:")
            for name, n in sorted(unresolved.items(), key=lambda kv: -kv[1]):
                self.stdout.write(f"  {name}: {n}")
