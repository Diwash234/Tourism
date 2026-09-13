from django.core.management.base import BaseCommand
from tourist.retention import apply_retention_policy


class Command(BaseCommand):
    help = "Preview or apply database retention windows for ephemeral personal records."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Delete eligible ephemeral records; default is dry-run")

    def handle(self, *args, **options):
        result = apply_retention_policy(dry_run=not options["apply"])
        mode = "DRY RUN" if result["dry_run"] else "APPLIED"
        self.stdout.write(f"{mode}: {result['total']} eligible records")
        for name, count in result["records"].items(): self.stdout.write(f"  {name}: {count}")
        if result["official_risk_preserved"]: self.stdout.write("Official risk records: preserved")
