from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """GPS fix quality on the user.

    Numbered after 0086 so the migration graph stays linear. Earlier numbers from this
    work (0083, then 0086) collided with migrations added on main, which left
    two leaf nodes and made `migrate` refuse to run.
    """

    dependencies = [
        ("tourist", "0086_clean_phone_artifacts"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="gps_accuracy_m",
            field=models.FloatField(
                blank=True, null=True, help_text="Device-reported accuracy in metres"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="gps_recorded_at",
            field=models.DateTimeField(
                blank=True, null=True, help_text="When the device took the fix"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="gps_validated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="gps_validation_state",
            field=models.CharField(
                blank=True,
                max_length=20,
                help_text="precise / approximate / unusable",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="gps_validation_reasons",
            field=models.JSONField(blank=True, default=list),
        ),
    ]


