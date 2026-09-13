# Generated data migration: classify existing records' provenance.
from django.db import migrations


def backfill(apps, schema_editor):
    Destination = apps.get_model("tourist", "Destination")
    # Records created through the platform by a user account -> user_suggested;
    # everything else predates admin tracking and came from the dataset import.
    Destination.objects.exclude(created_by__isnull=True).update(provenance="user_suggested")
    Destination.objects.filter(created_by__isnull=True).update(provenance="imported")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0068_destination_correction_reason_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
