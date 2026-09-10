# Seeded default for the admin-configurable road-routing provider (master
# spec §6/§69). Admins edit or disable it via the CMS "settings" resource —
# no code change needed. HTTPS base URLs only; see routing_service.provider_config.
from django.db import migrations


DEFAULT_VALUE = {
    "enabled": True,
    "base_url": "https://router.project-osrm.org/route/v1/driving",
    "api_key": "",
    "note": "OSRM demo server — replace with your own OSRM/GraphHopper instance for production traffic.",
}


def seed_routing_provider(apps, schema_editor):
    SiteSetting = apps.get_model("tourist", "SiteSetting")
    SiteSetting.objects.get_or_create(
        key="routing_provider",
        defaults={
            "value": DEFAULT_VALUE,
            "description": "Road-routing provider for real driving distances (OSRM protocol). HTTPS only.",
            "is_public": False,
        },
    )


def unseed_routing_provider(apps, schema_editor):
    SiteSetting = apps.get_model("tourist", "SiteSetting")
    SiteSetting.objects.filter(key="routing_provider").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0067_support_navigation_links"),
    ]

    operations = [
        migrations.RunPython(seed_routing_provider, unseed_routing_provider),
    ]
