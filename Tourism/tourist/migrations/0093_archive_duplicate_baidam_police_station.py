"""Archive the confirmed duplicate Baidam police-station listing.

Rows 222 and 223 describe the same recorded station: identical name and
coordinates, with the more specific Baidam address retained.  The less
specific Kaski listing remains in the database for audit history but is hidden
from public service results rather than deleted.
"""
from django.db import migrations


KEEP_ID = 222
DUPLICATE_ID = 223


def archive_duplicate(apps, schema_editor):
    PoliceStation = apps.get_model("tourist", "PoliceStation")
    keep = PoliceStation.objects.filter(
        pk=KEEP_ID,
        name="Police Station Baidam",
        latitude=28.215,
        longitude=83.956,
    ).first()
    duplicate = PoliceStation.objects.filter(
        pk=DUPLICATE_ID,
        name="Police Station Baidam",
        latitude=28.215,
        longitude=83.956,
    ).first()
    if keep and duplicate:
        duplicate.is_archived = True
        duplicate.save(update_fields=["is_archived"])


def unarchive_duplicate(apps, schema_editor):
    PoliceStation = apps.get_model("tourist", "PoliceStation")
    PoliceStation.objects.filter(
        pk=DUPLICATE_ID,
        name="Police Station Baidam",
        latitude=28.215,
        longitude=83.956,
    ).update(is_archived=False)


class Migration(migrations.Migration):
    dependencies = [("tourist", "0092_merge_main_handoff")]

    operations = [migrations.RunPython(archive_duplicate, unarchive_duplicate)]
