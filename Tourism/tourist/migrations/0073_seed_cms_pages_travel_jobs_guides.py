"""Seed ManagedPage rows for the Travel Planner, Tourism Jobs and Guides
pages so the Admin CMS (Website -> Page Editor) can manage their intro and
extra sections — same pattern as the earlier page-CMS seeds. Idempotent
(get_or_create): existing installs with hand-created rows are untouched."""
from django.db import migrations


def seed(apps, schema_editor):
    Page = apps.get_model("tourist", "ManagedPage")
    for key, route, title in (
        ("travel", "/travel", "Travel Planner"),
        ("tourism-jobs", "/tourism-jobs", "Tourism Work & Gigs"),
        ("guides", "/guides", "Verified Local Guides"),
    ):
        Page.objects.get_or_create(
            key=key,
            defaults={"route": route, "title": title, "status": "published"},
        )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tourist", "0072_destination_meta_description_destination_meta_robots_and_more")]

    operations = [migrations.RunPython(seed, reverse)]
