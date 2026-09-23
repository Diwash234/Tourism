"""Seed an admin-editable fare card for transport cost ESTIMATES.

Values are rough Kathmandu-typical figures used only to render labelled
estimates; every value is editable/deletable in Django admin (SiteSetting
'fare_card'). Deleting a key hides that cost as 'Information unavailable'.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    SiteSetting = apps.get_model("tourist", "SiteSetting")
    row, _ = SiteSetting.objects.get_or_create(
        key="fare_card",
        defaults={
            "value": {
                "taxi_base_npr": 100,
                "taxi_per_km_npr": 50,
                "bicycle_rental_npr": 200,
                "bus_typical_npr": 30,
            },
            "description": "Admin-editable transport fare estimates (NPR). Rough typicals; labelled as estimates in the UI. Remove a key to hide that cost.",
        },
    )


def backwards(apps, schema_editor):
    SiteSetting = apps.get_model("tourist", "SiteSetting")
    SiteSetting.objects.filter(key="fare_card").delete()


class Migration(migrations.Migration):
    dependencies = [("tourist", "0069_province_district")]
    operations = [migrations.RunPython(forwards, backwards)]
