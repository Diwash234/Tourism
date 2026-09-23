# Data migration: purge the legacy "Digital Nepal Tourism Platform" brand from
# stored data (branding setting + page titles/meta). The old seed migrations
# (0026/0034/0036/0037) are left immutable; this runs after them on fresh
# installs and once on existing DBs. Idempotent.
from django.db import migrations

OLD_LONG = "Digital Nepal Tourism Platform"
OLD_SHORT = "Digital Nepal Tourism"
NEW = "Nepal Yatra"


def scrub(value):
    if not isinstance(value, str):
        return value, False
    cleaned = value.replace(OLD_LONG, NEW).replace(OLD_SHORT, NEW)
    return cleaned, cleaned != value


def forwards(apps, schema_editor):
    Setting = apps.get_model("tourist", "SiteSetting")
    branding = Setting.objects.filter(key="branding").first()
    if branding and isinstance(branding.value, dict):
        changed = False
        for key, val in list(branding.value.items()):
            cleaned, did = scrub(val)
            if did:
                branding.value[key] = cleaned
                changed = True
        if changed:
            branding.save()

    Page = apps.get_model("tourist", "ManagedPage")
    for page in Page.objects.all():
        changed = False
        for field in ("title", "meta_description", "seo_title"):
            cleaned, did = scrub(getattr(page, field, None))
            if did:
                setattr(page, field, cleaned)
                changed = True
        if changed:
            page.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tourist", "0050_navbar_nepal_yatra_structure")]
    operations = [migrations.RunPython(forwards, backwards)]
