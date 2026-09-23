import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tourist.risk_ingestion import PROVIDERS, ingest_records


class Command(BaseCommand):
    help = "Ingest a normalized, reviewed DHM/BIPAD/admin/news JSON risk feed"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
        parser.add_argument("--verified", action="store_true", help="Mark sourced authoritative rows verified")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        records = payload.get("records", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise CommandError("Feed must be a JSON list or an object containing a records list.")
        summary = ingest_records(records, options["provider"], verified=options["verified"])
        self.stdout.write(self.style.SUCCESS(json.dumps(summary, indent=2)))
