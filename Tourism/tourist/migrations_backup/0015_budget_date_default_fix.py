from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    """
    ADDED: Budget.date's default was `timezone.now` (a datetime
    callable) on a DateField -- confirmed live this crashed every
    budget-entry creation with a 500 on the response serialization
    step, even though the record itself saved fine. Fixed to
    `timezone.localdate` (Django's own utility for a real `date`
    default). This is a Python-level default-callable change only --
    no column type change, no data migration needed, safe on its own,
    same as 0012/0013 before it.
    """

    dependencies = [
        ("tourist", "0014_itinerary_and_related_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="budget",
            name="date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]