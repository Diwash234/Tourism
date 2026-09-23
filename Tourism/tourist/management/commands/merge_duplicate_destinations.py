"""Conservatively merge duplicate destinations (register DEF-011).

Two APPROVED public records count as duplicates ONLY when ALL hold:
  * identical name AND district (district non-blank),
  * coordinates within --max-distance metres (default 100 m).

Same-named records farther apart are treated as distinct real places
and are never touched (72 of 114 observed pairs are legitimately far).

The richest record survives; sparse twins are ARCHIVED (never deleted).
Non-empty fields on a twin fill the survivor's blanks, its gallery
images move across (URL-deduplicated), and every merge is recorded in
DuplicateDecision (merged_snapshot) + DestinationAuditLog on both rows.

Usage:
    python manage.py merge_duplicate_destinations             # dry run
    python manage.py merge_duplicate_destinations --apply     # write
"""
import math

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Destination, DestinationAuditLog, DuplicateDecision

FILL_FIELDS = [
    "description", "short_description", "opening_hours", "entry_fee",
    "contact_phone", "contact_email", "website", "best_time_to_visit",
    "address", "municipality", "ward_number", "altitude",
    "cultural_significance", "travel_safety_tips", "religious_significance",
]


def haversine_m(lat1, lon1, lat2, lon2):
    la1, lo1, la2, lo2 = map(math.radians, [float(lat1), float(lon1),
                                            float(lat2), float(lon2)])
    return 6371000 * 2 * math.asin(math.sqrt(
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


def richness(d):
    score = sum(1 for f in FILL_FIELDS if getattr(d, f, None) not in (None, ""))
    score += 2 * d.gallery.count()
    score += 3 * d.reviews.count()
    score += int(d.ratings_count or 0)
    return score


class Command(BaseCommand):
    help = "Merge same-name same-district destinations within 100 m; archive twins."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Actually write; default is a dry run.")
        parser.add_argument("--max-distance", type=float, default=100.0,
                            help="Max metres between coordinates to consider duplicates.")

    def handle(self, *args, **options):
        max_d = options["max_distance"]
        pub = (Destination.objects
               .filter(status="approved", is_active=True)
               .exclude(district="").exclude(district=None)
               .exclude(latitude=None).exclude(longitude=None))

        groups = {}
        for row in pub.values("id", "name", "district", "latitude", "longitude"):
            key = (row["name"].strip().lower(), row["district"])
            groups.setdefault(key, []).append(row)

        clusters = []
        for (_name, district), rows in groups.items():
            if len(rows) < 2:
                continue
            # single-linkage clustering by distance
            assigned = []
            for row in rows:
                placed = False
                for cluster in assigned:
                    if any(haversine_m(row["latitude"], row["longitude"],
                                       m["latitude"], m["longitude"]) <= max_d
                           for m in cluster):
                        cluster.append(row)
                        placed = True
                        break
                if not placed:
                    assigned.append([row])
            clusters.extend(c for c in assigned if len(c) >= 2)

        merged = archived = 0
        for cluster in clusters:
            objs = list(Destination.objects.filter(
                id__in=[r["id"] for r in cluster]))
            keeper = max(objs, key=lambda d: (richness(d), -d.id))
            twins = [d for d in objs if d.id != keeper.id]
            if not options["apply"]:
                self.stdout.write(
                    f"WOULD MERGE '{keeper.name}' ({district_of(keeper)}): "
                    f"keep #{keeper.id} ({richness(keeper)} pts), archive "
                    f"{[t.id for t in twins]}")
                merged += 1
                archived += len(twins)
                continue
            with transaction.atomic():
                for twin in twins:
                    # fill the keeper's blanks from the twin
                    filled = []
                    for f in FILL_FIELDS:
                        if getattr(keeper, f, None) in (None, "") and \
                                getattr(twin, f, None) not in (None, ""):
                            setattr(keeper, f, getattr(twin, f))
                            filled.append(f)
                    # move gallery images (skip URL duplicates)
                    keeper_urls = set(keeper.gallery.values_list(
                        "external_url", flat=True))
                    for img in twin.gallery.all():
                        if img.external_url in keeper_urls:
                            continue
                        img.destination = keeper
                        img.save(update_fields=["destination"])
                        keeper_urls.add(img.external_url)
                    snapshot = {"id": twin.id, "slug": twin.slug,
                                "filled_fields": filled,
                                "latitude": str(twin.latitude),
                                "longitude": str(twin.longitude)}
                    twin.status = Destination.SubmissionStatus.ARCHIVED
                    twin.is_active = False
                    twin.save()
                    keeper.save()
                    DuplicateDecision.objects.create(
                        destination_a=keeper, destination_b=twin,
                        verdict=DuplicateDecision.Verdict.MERGED,
                        surviving_id=keeper.id, merged_snapshot=snapshot,
                        reason=(f"auto-merge: identical name+district within "
                                f"{max_d:.0f} m (merge_duplicate_destinations)"))
                    DestinationAuditLog.objects.create(
                        destination=keeper,
                        action=DestinationAuditLog.Action.EDITED,
                        note=f"Merged duplicate #{twin.id} ({twin.slug}); "
                             f"filled: {filled or 'nothing'}")
                    DestinationAuditLog.objects.create(
                        destination=twin,
                        action=DestinationAuditLog.Action.ARCHIVED,
                        note=f"Archived as duplicate of #{keeper.id} "
                             f"({keeper.slug})")
                    archived += 1
                merged += 1

        verb = "Merged" if options["apply"] else "Would merge"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {merged} duplicate cluster(s); archived {archived} twin(s)."
            + ("" if options["apply"] else " Re-run with --apply to write.")))


def district_of(d):
    return d.district or ""
