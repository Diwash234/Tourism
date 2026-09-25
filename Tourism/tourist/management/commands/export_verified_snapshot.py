"""Export the privacy-safe canonical tourism data snapshot as JSON."""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from tourist.verified_snapshot import build_snapshot_payload, write_payload


class Command(BaseCommand):
    help = "Export sourced public tourism records to the canonical JSON snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(Path(settings.BASE_DIR) / "dataset" / "verified_tourism_data.json"),
            help="Destination JSON path.",
        )
        parser.add_argument(
            "--as-of",
            required=True,
            help="ISO-8601 cutoff used for scheduled/published records.",
        )

    def handle(self, *args, **options):
        as_of = None
        if options.get("as_of"):
            as_of = parse_datetime(options["as_of"])
            if as_of is None:
                raise CommandError("--as-of must be a valid ISO-8601 timestamp")
            as_of = timezone.make_aware(as_of) if timezone.is_naive(as_of) else as_of

        payload = build_snapshot_payload(as_of=as_of)
        output = write_payload(options["output"], payload)
        counts = payload["counts"]
        self.stdout.write(self.style.SUCCESS(
            f"Verified data JSON written: {output} "
            f"({sum(counts.values())} records, sha256={payload['records_sha256']})"
        ))
        for model, count in counts.items():
            self.stdout.write(f"  {model}: {count}")
