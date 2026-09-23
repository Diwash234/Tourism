"""
Curate out records that were imported from OSM but are not tourist places.

These are company offices / government boards that slipped in during bulk
OSM import and were published as destinations (e.g. an engineering
consultancy filed under "Viewpoints & Lookouts", a bank under "Lakes").

Archiving (status=archived, is_active=False) — never deleting — so the
records stay auditable and recoverable. Real travel agencies, trekking
operators and hotels (whose Nepali corporate names contain "Pvt Ltd") are
deliberately NOT in this list.

Idempotent: safe to run repeatedly; already-archived rows are skipped.
"""
from django.core.management.base import BaseCommand

from tourist.models import Destination

# slug -> why it is not a tourist destination
NON_TOURIST = {
    "aviyantra-engineering-consultancy":
        "engineering consultancy office (was filed under Viewpoints)",
    "pioneer-wires-pvt-ltdsards-group-office":
        "wire supplier company office",
    "wave-engineering":
        "engineering firm office",
    "salute-gorkha-training-center-pvt-ltd":
        "private training centre, not a place to visit",
    "fewa-bikash-bank-limited":
        "bank branch misfiled under the 'Lakes' category "
        "(bank directories serve these)",
    "abs-technologies-pvt-ltd":
        "IT company office",
    "hisila-suppliers-pvt-ltd":
        "parts/supplies company office",
    "blue-horizon-pvt-ltd":
        "company office with boilerplate description, unverifiable as a "
        "tourist destination",
    "road-construction-information-board":
        "government road board office",
    "road-construction-information-board-2":
        "government road board office (duplicate of the above)",
}


class Command(BaseCommand):
    help = "Archive OSM-imported records that are company offices, not tourist destinations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report what would be archived without changing anything",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        changed = 0
        for slug, reason in NON_TOURIST.items():
            rows = Destination.objects.filter(slug=slug)
            for row in rows:
                if row.status == Destination.SubmissionStatus.ARCHIVED and not row.is_active:
                    self.stdout.write(f"  skip   {slug} (already archived)")
                    continue
                self.stdout.write(f"  {'would ' if dry else ''}archive {slug}: {reason}")
                if not dry:
                    row.status = Destination.SubmissionStatus.ARCHIVED
                    row.is_active = False
                    row.save(update_fields=["status", "is_active"])
                changed += 1
        verb = "Would archive" if dry else "Archived"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {changed} record(s). "
            f"Public destinations: "
            f"{Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED).count()}"
        ))
