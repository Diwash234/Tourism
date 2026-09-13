"""Production data pipeline orchestrator — the explicit system component:

    SOURCE -> IMPORT -> NORMALIZE -> DEDUPLICATE -> VALIDATE
           -> VERIFICATION QUEUE -> ADMIN REVIEW -> PUBLISH

Each stage already exists as its own tool; this command chains the
operational stages in order and prints a single pipeline health report, so
"keep the national dataset fresh" is one scheduled job instead of tribal
knowledge. Every stage runs in its SAFE mode by default (imports dedupe by
external_id; verification expiry and duplicate detection are report-only) —
pass --apply to let the mutating stages write.

    python manage.py run_data_pipeline              # health report
    python manage.py run_data_pipeline --apply      # + expire stale verifications

Stages:
  1. import       import_osm_destinations  (bundled OSM CSV; external_id dedupe)
  2. normalize    normalize_district_names (canonical district/province)
  3. freshness    flag_stale_verifications (--flag only with --apply)
  4. dedupe       detect_duplicate_destinations (JSON report for admin review)
  5. queue        DestinationCandidate verification-queue status (admin reviews
                  candidates in /admin/discovery; publishing stays a human act)
"""
import os
from datetime import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the full data-maintenance pipeline in safe (report) mode; --apply enables writes."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Allow mutating stages (verification expiry) to write")
        parser.add_argument("--report-dir", default=None,
                            help="Directory for stage reports (default: dataset/osm_reports)")

    def handle(self, *args, **options):
        from django.conf import settings
        from tourist.models import Destination, DestinationCandidate

        apply_writes = options["apply"]
        report_dir = options["report_dir"] or os.path.join(settings.BASE_DIR, "dataset", "osm_reports")
        os.makedirs(report_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        self.stdout.write("== 1/5 import (bundled OSM dataset, deduped by external_id) ==")
        call_command("import_osm_destinations")

        self.stdout.write("== 2/5 normalize (canonical district/province spellings) ==")
        call_command("normalize_district_names", *([] if apply_writes else ["--dry-run"]))

        self.stdout.write("== 3/5 freshness (verification expiry) ==")
        freshness_args = ["--interval-days", "180",
                          "--report", os.path.join(report_dir, f"freshness-{stamp}.json")]
        if apply_writes:
            freshness_args.append("--flag")
        call_command("flag_stale_verifications", *freshness_args)

        self.stdout.write("== 4/5 deduplicate (candidate report for admin review) ==")
        dupes_path = os.path.join(report_dir, f"duplicate_candidates-{stamp}.json")
        call_command("detect_duplicate_destinations", "--report", dupes_path)

        self.stdout.write("== 5/5 verification queue (admin review backlog) ==")
        total = Destination.objects.count()
        approved = Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED).count()
        pending = Destination.objects.filter(status=Destination.SubmissionStatus.PENDING).count()
        candidates = DestinationCandidate.objects.count()
        self.stdout.write(
            f"destinations: total={total} approved+active={approved} pending_review={pending} | "
            f"research candidates in queue: {candidates}"
        )
        self.stdout.write(
            "NEXT HUMAN STEPS: review high-confidence duplicates in "
            f"{dupes_path} (merge via POST /api/v1/admin/destinations/merge/), "
            "approve/reject pending submissions and research candidates in the admin."
        )
