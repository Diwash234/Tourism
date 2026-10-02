"""Reconcile the public catalogue with the curated reference data.

Boot hygiene for the public browse surfaces, run from the entrypoint (both
the heavy ``run_data_repairs`` path and the lightweight Render boot path).
Idempotent, network-free:

1. Hide OSM-CSV-imported junk rows.  ``import_osm_destinations`` bulk-creates
   Destination rows straight from ``destinations_clean.csv``: empty
   ``cover_image``, mojibake names, ``type`` of ``node``/``way``/``relation``.
   They crowd page 1 of every ``ordering=name`` browse (the "image
   unavailable / data unavailable" report) and leak into itinerary
   candidates.  Candidate rows must carry the full marker signature
   (``provenance=imported`` + non-null ``imported_at`` + a CSV OSM ``type`` +
   no submitter/creator) **and** a pk that is NOT owned by the tracked seed
   files.

   The seed-pk exclusion is load-bearing, not belt-and-braces: the importer's
   enrich path stamps ``imported_at`` onto existing seed rows it matches by
   ``external_id``, and ``convert_dataset_to_fixture`` copies the CSV
   ``type`` into the same rows — so a marker-only rule would happily hide
   thousands of legitimate seed destinations.  Seed rows are identified from
   ``dataset/data.json`` (destination ids) and
   ``dataset/verified_tourism_data.json`` (fixture pks).  If neither file can
   be read, hiding is skipped entirely rather than guessing.

   Only ``is_active=False`` is ever written — the canonical rule
   ``Destination.publicly_visible`` filters on — so hidden rows vanish from
   listing, detail, search, map, related and sitemap endpoints at once.  The
   command never reactivates anything in normal mode: ``is_active=False`` is
   an admin decision.  (``--restore-hidden-seed`` exists for recovering rows
   a marker-only run hid by mistake; it touches seed-pk rows carrying the
   OSM signature and nothing else.)

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
        parser.add_argument(
            "--restore-hidden-seed",
            action="store_true",
            help=(
                "Recovery only: reactivate seed-pk rows that carry the full "
                "OSM import signature (rows a marker-only run hid by "
                "mistake). Never touches non-seed rows or non-OSM-signature "
                "rows, so admin-hidden rows outside that signature stay "
                "hidden."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        restored = 0
        if options["restore_hidden_seed"]:
            restored = self.restore_hidden_seed_rows()

        hidden = 0
        if options["skip_hide_osm"]:
            pass
        elif options["restore_hidden_seed"]:
            pass  # a restore run must not immediately re-hide the same rows
        else:
            hidden = self.hide_osm_rows()

        if options["skip_featured"]:
            flagged, missing = 0, []
        else:
            flagged, missing = self.pin_featured()

        active = Destination.objects.filter(is_active=True).count()
        summary = (
            f"reconcile_catalogue: deactivated={hidden} restored={restored} "
            f"featured_pinned={flagged} active_destinations={active}"
        )
        if missing:
            shown = ",".join(missing[:5])
            if len(missing) > 5:
                shown += f",...(+{len(missing) - 5} more)"
            summary += f" featured_missing={shown}"
        self.stdout.write(self.style.SUCCESS(summary))

    def load_seed_pks(self):
        """pks owned by the tracked seed files — never deactivated.

        Returns ``(pk_set, sources)``. An empty set means "unknown": callers
        must skip hiding rather than guess.
        """
        tourism_dir = Path(__file__).resolve().parents[3]
        pks = set()
        sources = []

        # data.json: {"destinations": {"<id>": {...}}, ...} — ids cover the
        # verified fixture pks plus the extra CSV-era rows (superset).
        path = tourism_dir / "dataset" / "data.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                dests = data.get("destinations") if isinstance(data, dict) else None
                if isinstance(dests, dict):
                    for key in dests:
                        try:
                            pks.add(int(key))
                        except (TypeError, ValueError):
                            continue
                    sources.append(f"data.json:{len(pks)}")
            except Exception as exc:  # unreadable file -> fall through to fixture
                self.stdout.write(self.style.WARNING(f"reconcile_catalogue: data.json unreadable ({exc})"))

        # verified snapshot: {"records": [{"model": "tourist.destination",
        # "pk": N, ...}]} — the authoritative fixture pk list.
        path = tourism_dir / "dataset" / "verified_tourism_data.json"
        if path.is_file():
            try:
                before = len(pks)
                data = json.loads(path.read_text(encoding="utf-8"))
                for rec in data.get("records", []):
                    if rec.get("model") == "tourist.destination":
                        pks.add(rec.get("pk"))
                pks.discard(None)
                sources.append(f"fixture:+{len(pks) - before}")
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"reconcile_catalogue: fixture unreadable ({exc})"))

        return pks, sources

    def _osm_marker_rows(self):
        """Rows carrying the full OSM bulk-import signature, active only."""
        return Destination.objects.filter(
            provenance=Destination.Provenance.IMPORTED,
            imported_at__isnull=False,
            type__in=OSM_TYPES,
            is_active=True,
            is_user_submitted=False,
            created_by__isnull=True,
        )

    def hide_osm_rows(self):
        """Deactivate OSM-created junk rows outside the seed pk set."""
        seed_pks, sources = self.load_seed_pks()
        if not seed_pks:
            self.stdout.write(
                self.style.WARNING(
                    "reconcile_catalogue: no seed pk set readable - hiding skipped (safety)"
                )
            )
            return 0

        candidates = self._osm_marker_rows().exclude(pk__in=seed_pks)
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
        self.stdout.write(f"reconcile_catalogue: seed pk set [{', '.join(sources)}] excluded from hiding")
        return total

    def restore_hidden_seed_rows(self):
        """Reactivate seed rows carrying the OSM signature (recovery tool).

        Only used after a marker-only incident: the pk set pins these to
        seed-owned rows, the signature pins them to rows that were hidden by
        the OSM-hiding logic (an admin hiding a seed row would normally flip
        status/provenance, not leave the bulk-import stamp intact).
        """
        seed_pks, _ = self.load_seed_pks()
        if not seed_pks:
            self.stdout.write(
                self.style.WARNING("reconcile_catalogue: no seed pk set readable - restore skipped")
            )
            return 0
        return (
            Destination.objects.filter(pk__in=seed_pks, is_active=False)
            .filter(
                provenance=Destination.Provenance.IMPORTED,
                imported_at__isnull=False,
                type__in=OSM_TYPES,
                is_user_submitted=False,
                created_by__isnull=True,
            )
            .update(is_active=True)
        )

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
