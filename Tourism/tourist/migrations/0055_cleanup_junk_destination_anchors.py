# Junk destination-anchor cleanup (follow-up to the 0053 hotel dedup audit).
#
# The dedup audit surfaced duplicate hotel rows that were attached to
# business-name destination records ("Hotel Kutumba", "Hotel peacock",
# "Wildlife Camp" — all category=hotel). Those anchors are import artefacts:
# the hotels they point at physically sit in Sauraha (Ratnanagar, Chitwan)
# and Kupandole (Lalitpur). Bulk-archiving name-hint matches is NOT done
# here on purpose — the 4k+ hint-matching rows are mostly legitimate
# homestay/lodge/eco-tourism content, and the ~2.9k category=hotel
# destinations are the platform's intentional accommodation inventory
# (served by the type=hotel listing view).
#
# This migration therefore fixes exactly the audited artefacts:
#   1. Re-point every hotel attached to the three junk anchors at the proper
#      town destination (Sauraha / Lalitpur (Patan)), so no hotel loses a
#      public destination.
#   2. Archive the anchors (is_active=False + archived_at, retention-safe —
#      same pattern as DestinationViewSet.perform_destroy).
# Lookups are by name+category and no-op when rows are absent (portable).
from django.db import migrations

JUNK_TO_TOWN = [
    ("hotel peacock", "sauraha"),
    ("wildlife camp", "sauraha"),
    ("hotel kutumba", "lalitpur (patan)"),
]


def cleanup(apps, schema_editor):
    Destination = apps.get_model("tourist", "Destination")
    Hotel = apps.get_model("tourist", "Hotel")
    moved_total = 0
    for junk_name, town_name in JUNK_TO_TOWN:
        junk = Destination.objects.filter(name__iexact=junk_name, category__slug="hotel").first()
        if not junk:
            continue
        town = (
            Destination.objects.filter(name__iexact=town_name, is_active=True)
            .exclude(pk=junk.pk)
            .first()
        )
        if town:
            moved = Hotel.objects.filter(destination=junk).update(destination=town)
            moved_total += moved
        junk.is_active = False
        junk.status = "archived"
        junk.save(update_fields=["is_active", "status", "updated_at"])
        print(f"\n[0055] Archived junk anchor '{junk.name}' (hotels re-pointed: {town.name if town else 'none found'})")
    if moved_total:
        print(f"[0055] Re-pointed {moved_total} hotel rows to their real town destinations.")


def noop_reverse(apps, schema_editor):
    # Retention-safe: archived anchors are not resurrected automatically.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0054_complete_page_inventory"),
    ]

    operations = [
        migrations.RunPython(cleanup, noop_reverse),
    ]
