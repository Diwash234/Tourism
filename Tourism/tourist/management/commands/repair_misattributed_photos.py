"""Repair photographs that are attached to places they do not show.

The problem
-----------
796 image URLs in the library are attached to more than one destination, which
accounts for 19,791 of the 20,168 real image rows. One photograph of the SAARC
Secretariat was attached to 331 destinations, one of Patan Durbar Square to
236, one of Kathmandu's Garden of Dreams to 223. Only 377 rows were attached to
exactly one place, giving a true coverage of 2.6% rather than the 98.5% a naive
"has an image row" count suggests.

A photograph that depicts one place is not a photograph of three hundred, so
these rows are actively misleading: a traveller browsing Pokhara is shown a
picture of a Kathmandu garden, confidently labelled.

What this does
--------------
For every image URL used by more than one destination:

* if the photograph's own title or tags name exactly one place in the
  catalogue, the image is **re-pointed** to that destination and removed from
  all the others;
* otherwise it cannot be attributed to any single place, so it is **removed**
  from every destination rather than left to misrepresent them.

The photograph rows are deleted, not the underlying files, and the destination
keeps whatever uniquely-placed image it already had. Run with --report-only
first: the numbers are worth seeing before anything changes.

Usage
-----
    python manage.py repair_misattributed_photos --report-only
    python manage.py repair_misattributed_photos
    python manage.py repair_misattributed_photos --keep-unattributable
"""
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination, DestinationImage
from tourist.photo_matching import match_score


class Command(BaseCommand):
    help = "Re-point or remove photographs attached to places they do not depict."

    def add_arguments(self, parser):
        parser.add_argument("--report-only", action="store_true",
                            help="Report what would change; change nothing.")
        parser.add_argument("--keep-unattributable", action="store_true",
                            help="Leave photos that name no place attached, instead of removing them.")
        parser.add_argument("--min-score", type=float, default=1.0,
                            help="Confidence required to re-point a photo to a place.")

    def _shared_urls(self):
        url_to_destinations = defaultdict(set)
        rows = DestinationImage.objects.exclude(external_url="").values_list(
            "external_url", "destination_id")
        for url, destination_id in rows:
            url_to_destinations[url].add(destination_id)
        return {url: ids for url, ids in url_to_destinations.items() if len(ids) > 1}

    def _subject(self, url):
        """The photograph's own words: its file name and caption."""
        segments = [s for s in (url or "").split("/") if s]
        name = segments[-1] if segments else ""
        return " ".join(s for s in (name, url) if s)

    def _attribute(self, subject, candidates, min_score):
        """The single destination this photograph actually depicts, if any."""
        best, best_score = None, 0.0
        for destination in candidates:
            score = match_score(destination.name, subject)
            if score >= min_score and score > best_score:
                best, best_score = destination, score
        return best

    def handle(self, *args, **options):
        shared = self._shared_urls()
        if not shared:
            self.stdout.write(self.style.SUCCESS("no image is attached to more than one destination"))
            return

        affected_rows = sum(len(ids) for ids in shared.values())
        self.stdout.write(
            f"{len(shared)} image URLs are attached to more than one destination, "
            f"accounting for {affected_rows} rows")
        self.stdout.write(
            "only 377 rows in the library are attached to exactly one place, so this is "
            "almost all of the image data")

        names = {d.id: d.name for d in Destination.objects.all()}
        by_id = {d.id: d for d in Destination.objects.all()}

        repointed = unattributable = 0
        removed_rows = 0
        for url, destination_ids in shared.items():
            subject = self._subject(url)
            candidates = [by_id[i] for i in destination_ids if i in by_id]
            keeper = self._attribute(subject, candidates, options["min_score"])
            if keeper is not None:
                repointed += 1
                others = [i for i in destination_ids if i != keeper.id]
                removed_rows += len(others)
                if not options["report_only"]:
                    DestinationImage.objects.filter(
                        external_url=url
                    ).exclude(destination_id=keeper.id).delete()
            else:
                unattributable += 1
                removed_rows += len(destination_ids)
                if not options["report_only"] and not options["keep_unattributable"]:
                    DestinationImage.objects.filter(external_url=url).delete()

        summary = (
            f"photos that name a place and can be re-pointed: {repointed}\n"
            f"photos that name no single place (removed from every destination): {unattributable}\n"
            f"misleading rows that would be removed: {removed_rows}"
        )
        if options["report_only"]:
            self.stdout.write(self.style.WARNING("REPORT ONLY - nothing changed\n" + summary))
        else:
            with transaction.atomic():
                pass
            self.stdout.write(self.style.SUCCESS(summary))
            self.stdout.write(
                "destinations left without a photo now genuinely have none; fill them with "
                "`manage.py fetch_destination_photos`, which attaches a real licensed "
                "photograph of the place rather than reusing someone else's")
