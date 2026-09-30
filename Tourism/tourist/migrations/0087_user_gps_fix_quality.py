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
        # GPS fields already added by 0083_user_gps_fix_quality
    ]


