from django.db import migrations, models


class Migration(migrations.Migration):
    """
    ADDED: `manage.py makemigrations --dry-run` against the real
    db.sqlite3 revealed the `tourist` app's models.py has drifted from
    its migration history by ~40 changes, including DELETING 11 models
    (SharedTrip, SOSAlert, TrustedContact, LocationPing, Notification,
    DeviceToken, Attraction, CulturalActivity, FoodPlace,
    TravelExpenseFeedback, TravelRiskFeedback) -- these look like
    they're mid-move into new `safety`/`notifications` apps that were
    never finished. Running that full migration would drop tables
    holding real submitted data (SOS alerts, trusted emergency
    contacts) with no data-migration plan -- NOT something to do
    automatically. That needs a deliberate decision, so it's
    deliberately left alone here.

    This migration only adds the one field that's actually causing a
    real, confirmed 500 error on GET /api/v1/destinations/ right now:
    `content_ai_generated` on Destination is referenced by the
    serializer/view layer but was missing from the DB schema entirely.
    """

    dependencies = [
        ("tourist", "0011_merge_20260810_1247"),
    ]

    operations = [
        migrations.AddField(
            model_name="destination",
            name="content_ai_generated",
            field=models.BooleanField(
                default=False,
                help_text="True if description/best_time_to_visit were filled by AI generation rather than typed by a human.",
            ),
        ),
    ]