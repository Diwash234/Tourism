"""Audit duplicate/reused media across distinct places without deleting anything.

This specifically detects the failure mode where Lakeside, Mahendrapul,
Pokhara, etc. all point to the same generic city photo. It only reports and,
with --apply, clears the public promotion/cover flag for high-confidence
cross-place collisions; the underlying image rows/files remain intact.
"""
from collections import defaultdict
from django.core.management.base import BaseCommand
from tourist.models import DestinationImage


class Command(BaseCommand):
    help = "Find image URLs reused across unrelated destinations."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **opts):
        qs = DestinationImage.objects.select_related("destination").exclude(
            external_url=""
        ).order_by("id")
        if opts["limit"]:
            qs = qs[:opts["limit"]]

        owners = defaultdict(list)
        for row in qs.iterator():
            owners[row.external_url].append(row)

        collisions = 0
        changed = 0
        for url, rows in owners.items():
            destinations = {r.destination_id for r in rows if r.destination_id}
            if len(destinations) < 2:
                continue

            collisions += 1
            self.stdout.write(
                f"REUSED: {len(destinations)} destinations -> {url}"
            )

            if opts["apply"]:
                # Keep the rows/files, but do not allow one shared external
                # image to become the cover for several different places.
                for row in rows:
                    if row.is_cover or row.is_promoted:
                        row.is_cover = False
                        row.is_promoted = False
                        row.save(update_fields=["is_cover", "is_promoted", "updated_at"])
                        changed += 1

        self.stdout.write(self.style.SUCCESS(
            f"cross_place_duplicate_urls={collisions} flags_cleared={changed} apply={opts['apply']}"
        ))
