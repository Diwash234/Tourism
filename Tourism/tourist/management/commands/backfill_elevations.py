"""Fill Destination.elevation_m from the Copernicus DEM (via Open-Meteo).

    python manage.py backfill_elevations --fetch [--districts Solukhumbu,Mustang] [--limit N]
    python manage.py backfill_elevations --import-file dataset/destination_elevations.json
    python manage.py backfill_elevations --export-urls /tmp/urls.txt   # for offline fetching
    python manage.py backfill_elevations --write-file dataset/destination_elevations.json

Only coordinates with >= 3 decimals are looked up (see tourist/elevation.py).
"""

import json
import time
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tourist import elevation
from tourist.models import Destination


class Command(BaseCommand):
    help = "Backfill destination elevations from a cited DEM source."

    def add_arguments(self, parser):
        parser.add_argument("--fetch", action="store_true")
        parser.add_argument("--import-file")
        parser.add_argument("--export-urls")
        parser.add_argument("--write-file")
        parser.add_argument("--districts", default="")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--only-missing", action="store_true", default=True)
        parser.add_argument("--dry-run", action="store_true")

    def _targets(self, opts):
        qs = Destination.objects.filter(status=Destination.SubmissionStatus.APPROVED, is_active=True)
        if opts["only_missing"]:
            qs = qs.filter(elevation_m__isnull=True)
        districts = [d.strip() for d in opts["districts"].split(",") if d.strip()]
        if districts:
            qs = qs.filter(district__in=districts)
        targets = elevation.eligible_queryset(qs)
        return targets[: opts["limit"]] if opts["limit"] else targets

    def handle(self, *args, **opts):
        if opts["import_file"]:
            stats = elevation.load_data_file(opts["import_file"], dry_run=opts["dry_run"])
            self.stdout.write(self.style.SUCCESS(f"Import: {stats}"))
            return
        if opts["write_file"]:
            rows = Destination.objects.filter(elevation_m__isnull=False).order_by("id")
            records = [{"id": d.id, "slug": d.slug, "lat": float(d.latitude), "lon": float(d.longitude),
                        "elevation_m": d.elevation_m, "source": d.elevation_source,
                        "retrieved_at": d.elevation_retrieved_at.isoformat() if d.elevation_retrieved_at else None}
                       for d in rows]
            Path(opts["write_file"]).write_text(json.dumps({
                "source": elevation.DEM_SOURCE, "api": elevation.OPEN_METEO_ELEVATION,
                "min_coordinate_decimals": elevation.MIN_DECIMALS, "records": records}, indent=0))
            self.stdout.write(self.style.SUCCESS(f"Wrote {len(records)} records to {opts['write_file']}"))
            return

        targets = self._targets(opts)
        batches = [targets[i:i + elevation.BATCH_SIZE] for i in range(0, len(targets), elevation.BATCH_SIZE)]
        if opts["export_urls"]:
            with open(opts["export_urls"], "w") as fh:
                for batch in batches:
                    fh.write(json.dumps({"ids": [d.id for d in batch],
                                         "points": [[float(d.latitude), float(d.longitude)] for d in batch],
                                         "url": elevation.batch_url([(d.latitude, d.longitude) for d in batch])}) + "\n")
            self.stdout.write(self.style.SUCCESS(f"Exported {len(batches)} batches ({len(targets)} destinations)"))
            return
        if not opts["fetch"]:
            raise CommandError("Choose --fetch, --import-file, --export-urls or --write-file.")

        today = date.today().isoformat()
        total = 0
        for i, batch in enumerate(batches, 1):
            try:
                values = elevation.fetch_batch([(d.latitude, d.longitude) for d in batch])
            except Exception as exc:
                self.stderr.write(f"Batch {i}/{len(batches)} failed: {exc}")
                continue
            records = [{"id": d.id, "lat": float(d.latitude), "lon": float(d.longitude), "elevation_m": v,
                        "source": elevation.DEM_SOURCE, "retrieved_at": today}
                       for d, v in zip(batch, values) if v is not None]
            stats = elevation.apply_records(records, dry_run=opts["dry_run"])
            total += stats["applied"]
            self.stdout.write(f"Batch {i}/{len(batches)}: {stats}")
            time.sleep(1)
        self.stdout.write(self.style.SUCCESS(f"Applied {total} elevations."))
