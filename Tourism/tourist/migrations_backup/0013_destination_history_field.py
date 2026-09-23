from django.db import migrations, models


class Migration(migrations.Migration):
    """
    ADDED: same story as 0012_destination_content_ai_generated -- the
    `history` column already exists in the real database (confirmed via
    PRAGMA table_info: nullable TEXT) but was never declared on the
    Destination model. Confirmed live: DestinationWriteSerializer
    couldn't even reference `history` without a 500
    ("Field name `history` is not valid for model `Destination`"),
    caught while building the admin "Add Destination" form.

    This uses AlterField (not AddField) because the column is already
    physically present -- this only updates Django's migration state/
    field metadata to match reality, it doesn't touch the schema.

    Still deliberately excludes the other ~40 pending changes
    `makemigrations` keeps bundling in (deleting 11 models including
    SharedTrip/SOSAlert/TrustedContact -- the safety features). That
    remains a separate, deliberate decision, not something to slip in
    via an unrelated single-field fix.
    """

    dependencies = [
        ("tourist", "0012_destination_content_ai_generated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="destination",
            name="history",
            field=models.TextField(
                blank=True, null=True,
                help_text="Historical background of this destination, shown on its detail page.",
            ),
        ),
    ]