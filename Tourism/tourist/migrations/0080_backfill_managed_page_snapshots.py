from django.db import migrations


def backfill_page_snapshots(apps, schema_editor):
    ManagedPage = apps.get_model("tourist", "ManagedPage")
    for page in ManagedPage.objects.filter(status="published", is_enabled=True):
        page.published_snapshot = {
            "key": page.key,
            "route": page.route,
            "title": page.title,
            "meta_description": page.meta_description,
            "seo_title": page.seo_title,
            "og_image_url": page.og_image_url,
            "search_visible": page.search_visible,
            "is_enabled": page.is_enabled,
        }
        page.save(update_fields=["published_snapshot"])


def noop(apps, schema_editor):
    # Snapshot data is intentionally retained on reverse; no destructive reset.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0079_managed_page_published_snapshot"),
    ]

    operations = [
        migrations.RunPython(backfill_page_snapshots, noop),
    ]
