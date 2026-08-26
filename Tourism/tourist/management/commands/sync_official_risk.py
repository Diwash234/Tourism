import json

from django.core.management.base import BaseCommand, CommandError

from tourist.official_connectors import fetch_official_feed


class Command(BaseCommand):
    help = "Fetch configured normalized DHM/BIPAD feeds and ingest verified records"

    def add_arguments(self, parser):
        parser.add_argument("--provider", choices=["dhm", "bipad", "all"], default="all")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        providers = ["dhm", "bipad"] if options["provider"] == "all" else [options["provider"]]
        results = []
        for provider in providers:
            try:
                results.append(fetch_official_feed(provider, dry_run=options["dry_run"]))
            except Exception as exc:  # command boundary: report provider without hiding others
                results.append({"provider": provider, "configured": True, "ingested": False, "error": str(exc)})
        self.stdout.write(json.dumps(results, indent=2, default=str))
        failed = [result for result in results if result.get("error")]
        if failed:
            raise CommandError(f"{len(failed)} official provider sync(s) failed")
