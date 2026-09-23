"""
Tourism/tourist/management/commands/run_destination_discovery.py

CLI Management Command to execute Mass Destination Discovery, Deduplication,
and Quality Scoring across all 7 Provinces and 77 Districts of Nepal.
"""

from django.core.management.base import BaseCommand
from tourist.discovery_pipeline import DestinationDiscoveryPipeline
from tourist.models import DestinationCandidate, Destination, DiscoveryJob


class Command(BaseCommand):
    help = "Run the Mass Nepal Destination Discovery and Deduplication Pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=5000,
            help="Maximum number of candidate records to scan and process (default: 5000)"
        )
        parser.add_argument(
            "--province",
            type=str,
            default="",
            help="Filter discovery by target Province name (e.g. Gandaki, Bagmati, Karnali)"
        )
        parser.add_argument(
            "--district",
            type=str,
            default="",
            help="Filter discovery by target District name (e.g. Kaski, Mustang, Solukhumbu)"
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        province = options["province"]
        district = options["district"]

        self.stdout.write(self.style.NOTICE(
            f"Starting Destination Discovery Pipeline (Limit: {limit:,}, Province: '{province or 'All'}', District: '{district or 'All'}')..."
        ))

        pipeline = DestinationDiscoveryPipeline()
        summary = pipeline.run_discovery_from_datasets(
            target_province=province,
            target_district=district,
            limit=limit,
        )

        total_candidates = DestinationCandidate.objects.count()
        verified = DestinationCandidate.objects.filter(discovery_status="verified").count()
        duplicates = DestinationCandidate.objects.exclude(duplicate_status="none").count()
        needs_review = DestinationCandidate.objects.filter(discovery_status="needs_review").count()

        self.stdout.write(self.style.SUCCESS(
            f"""
======================================================
🇳🇵 NEPAL DESTINATION DISCOVERY COMPLETED
======================================================
Records Scanned:        {summary.get('scanned', 0):,}
Candidates Created:     {summary.get('created', 0):,}
Duplicates Prevented:   {summary.get('duplicates', 0):,}
High-Confidence Verified:{summary.get('verified', 0):,}
Errors:                 {summary.get('errors', 0):,}

Total Staging Candidates in DB: {total_candidates:,}
  - Verified Ready to Publish:  {verified:,}
  - Duplicate Matches Caught:   {duplicates:,}
  - In Review Queue:            {needs_review:,}
======================================================
"""
        ))
