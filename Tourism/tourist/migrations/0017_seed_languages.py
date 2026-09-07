"""Seed supported languages so the Settings language dropdown and the
frontend i18n store have real options (the table was empty)."""
from django.db import migrations

LANGS = [
    ("en", "English"),
    ("ne", "Nepali"),
    ("hi", "Hindi"),
    ("fr", "French"),
    ("de", "German"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("es", "Spanish"),
    ("it", "Italian"),
    ("ar", "Arabic"),
    ("ru", "Russian"),
    ("pt", "Portuguese"),
]


def seed(apps, schema_editor):
    Language = apps.get_model("tourist", "Language")
    for code, name in LANGS:
        Language.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})


def unseed(apps, schema_editor):
    Language = apps.get_model("tourist", "Language")
    Language.objects.filter(code__in=[c for c, _ in LANGS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0016_alter_destinationimage_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
