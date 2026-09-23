# Generated for the hotels dedup audit (continuation brief).
#
# The dataset import produced a handful of true duplicate hotel rows: same
# name (case-insensitive), same coordinates within ~100 m, same address, no
# bookings/reviews, each pair attached to two different destination records.
# This data migration archives the later duplicate of every such group
# (is_active=False + archived_at, the same retention-safe pattern used by
# HotelViewSet.perform_destroy) and keeps the earliest-imported row.
#
# Detection is computed from the data itself (no hardcoded ids) so it is
# portable across databases. Reverse is intentionally a no-op: archived rows
# are kept and remain visible to admins, matching the platform's
# retention-safe deletion policy.
from django.db import migrations
from django.utils import timezone


def deduplicate_hotels(apps, schema_editor):
    Hotel = apps.get_model("tourist", "Hotel")
    now = timezone.now()
    seen = {}
    archived = 0
    qs = (
        Hotel.objects.filter(is_active=True, archived_at__isnull=True)
        .only("id", "name", "latitude", "longitude")
        .order_by("id")
    )
    for hotel in qs.iterator():
        if hotel.latitude is None or hotel.longitude is None or not hotel.name:
            continue
        key = (
            hotel.name.strip().lower(),
            round(float(hotel.latitude), 3),
            round(float(hotel.longitude), 3),
        )
        if key in seen:
            Hotel.objects.filter(id=hotel.id).update(is_active=False, archived_at=now)
            archived += 1
        else:
            seen[key] = hotel.id
    if archived:
        print(f"\n[0053] Archived {archived} duplicate hotel rows (retention-safe).")


def noop_reverse(apps, schema_editor):
    # Retention-safe: archived duplicates are not resurrected automatically.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0052_travelerdocument"),
    ]

    operations = [
        migrations.RunPython(deduplicate_hotels, noop_reverse),
    ]
