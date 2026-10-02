"""Reconcile the public catalogue with the curated reference data.

Boot hygiene for the public browse surfaces, run from the entrypoint data
phase. Two idempotent, network-free fixes:

1. Hide OSM-CSV-imported junk rows.  ``import_osm_destinations`` bulk-creates
   Destination rows straight from ``destinations_clean.csv``: empty
   ``cover_image``, mojibake names, ``type`` of ``node``/``way``/``relation``.
   They crowd page 1 of every ``ordering=name`` browse (the "image
   unavailable / data unavailable" report) and leak into itinerary
   candidates.  The row markers distinguish them from every legitimate seed
   source with certainty:

   * fixture / data.json / load.json rows carry ``imported_at = NULL`` and an
     empty ``type`` (verified against all three tracked seed files),
   * user submissions set ``is_user_submitted`` or ``created_by``,
   * only rows carrying ALL of ``provenance=imported``, a non-null
     ``imported_at``, and a CSV OSM ``type`` are touched, and only to set
     ``is_active=False`` — the canonical rule ``Destination.publicly_visible``
     filters on, so they vanish from listing, detail, search, map, related
     and sitemap endpoints at once.

   The command never reactivates anything: ``is_active=False`` is an admin
   decision, and rows already hidden by hand stay hidden.

2. Pin the curated featured set from ``dataset/featured_destinations.json``.
   The CMS ``FeaturedDestination`` table is empty in production, and
   ``PublicFeaturedDestinationView`` falls back to
   ``Destination.objects.filter(is_featured=True, ...)`` — without pinned
   rows the homepage featured rail is empty and ``?featured=true`` returns
   nothing.  Rows are only ever added (an admin's own extra ``is_featured``
   flags are never cleared).

Running the command twice is a no-op; it prints what it changed.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination

#: The ``Type`` column values in destinations_clean.csv (all 12,838 rows are
#: one of these three, verified) — the OSM importer copies them verbatim.
OSM_TYPES = ("node", "way", "relation")


class Command(BaseCommand):
    help = (
        "Hide OSM-CSV-imported junk destinations from public surfaces and "
        "pin the curated featured set (idempotent, no network access)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-hide-osm",
            action="store_true",
            help="Do not deactivate OSM-imported junk rows.",
        )
        parser.add_argument(
            "--skip-featured",
            action="store_true",
            help="Do not pin the curated featured set.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        hidden = 0 if options["skip_hide_osm"] else self.hide_osm_rows()
        if options["skip_featured"]:
            flagged, missing = 0, []
        else:
            flagged, missing = self.pin_featured()

        active = Destination.objects.filter(is_active=True).count()
        summary = (
            f"reconcile_catalogue: deactivated={hidden} "
            f"featured_pinned={flagged} active_destinations={active}"
        )
        if missing:
            shown = ",".join(missing[:5])
            if len(missing) > 5:
                shown += f",...(+{len(missing) - 5} more)"
            summary += f" featured_missing={shown}"
        self.stdout.write(self.style.SUCCESS(summary))

    def hide_osm_rows(self):
        """Deactivate rows matching the exact OSM bulk-import signature.

        Only ``is_active`` is written; nothing else about a row — including
        rows an admin already deactivated — is ever changed.
        """
        candidates = Destination.objects.filter(
            provenance=Destination.Provenance.IMPORTED,
            imported_at__isnull=False,
            type__in=OSM_TYPES,
            is_active=True,
            is_user_submitted=False,
            created_by__isnull=True,
        )
        # Tracked in batches so the WHERE clause (and Postgres' plan) never
        # has to hold the whole junk set in one statement.
        total = 0
        while True:
            pks = list(candidates.values_list("pk", flat=True)[:2000])
            if not pks:
                break
            total += Destination.objects.filter(pk__in=pks).update(is_active=False)
            if len(pks) < 2000:
                break
        return total

    def pin_featured(self):
        """Set ``is_featured=True`` for every curated slug that exists.

        Never clears the flag on rows outside the file. Returns
        ``(rows_flagged, missing_slugs)``.
        """
        path = Path(__file__).resolve().parents[3] / "dataset" / "featured_destinations.json"
        if not path.is_file():
            self.stdout.write(
                self.style.WARNING(f"reconcile_catalogue: featured dataset not found at {path} - skipping")
            )
            return 0, []

        slugs = [s for s in json.loads(path.read_text(encoding="utf-8")).get("slugs", []) if s]
        if not slugs:
            return 0, []

        flagged = Destination.objects.filter(slug__in=slugs, is_featured=False).update(is_featured=True)
        found = set(Destination.objects.filter(slug__in=slugs).values_list("slug", flat=True))
        missing = sorted(set(slugs) - found)
        return flagged, missing
