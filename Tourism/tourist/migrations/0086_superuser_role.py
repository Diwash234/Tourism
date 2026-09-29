"""Superusers created with `createsuperuser` got the default role "tourist",
so the app labelled full administrators as "Traveller". Give existing
superusers that still carry the default role the super_admin role. Users with
any other explicitly chosen role are left untouched."""
from django.db import migrations


def fix_roles(apps, schema_editor):
    User = apps.get_model("tourist", "User")
    User.objects.filter(is_superuser=True, role="tourist").update(role="super_admin")


class Migration(migrations.Migration):
    dependencies = [("tourist", "0085_handoff_clear_missing_marker_phones")]

    operations = [migrations.RunPython(fix_roles, migrations.RunPython.noop)]
