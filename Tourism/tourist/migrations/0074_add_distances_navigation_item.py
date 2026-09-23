from django.db import migrations


def add_distances_item(apps, schema_editor):
    ManagedNavigationItem = apps.get_model("tourist", "ManagedNavigationItem")
    exists = ManagedNavigationItem.objects.filter(
        location="sidebar", route="/distances"
    ).exists()
    if exists:
        return
    # Placed right after "Navigation" (display_order 9, tie broken by id).
    ManagedNavigationItem.objects.create(
        location="sidebar",
        label="Distances & Directions",
        route="/distances",
        icon="distance",
        allowed_roles=[],
        display_order=9,
        is_active=True,
    )


def remove_distances_item(apps, schema_editor):
    ManagedNavigationItem = apps.get_model("tourist", "ManagedNavigationItem")
    ManagedNavigationItem.objects.filter(
        location="sidebar", route="/distances"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0073_seed_cms_pages_travel_jobs_guides"),
    ]

    operations = [
        migrations.RunPython(add_distances_item, remove_distances_item),
    ]
