"""Make Customer Support / feedback chat discoverable on the public site.

The support chat page (/support) and public feedback API existed, but nothing
linked to them outside the footer's deep link list — travellers could not
find them. Seeds managed navigation entries (admin can still edit, reorder,
or remove them from Website Content & Navigation).
"""

from django.db import migrations
from django.db.models import Max


def add_support_links(apps, schema_editor):
    Nav = apps.get_model("tourist", "ManagedNavigationItem")
    if not Nav.objects.filter(location="navbar", route="/support").exists():
        order = (Nav.objects.filter(location="navbar").aggregate(m=Max("display_order"))["m"] or 0) + 1
        Nav.objects.create(location="navbar", label="Support", route="/support", display_order=order, is_active=True)
    if not Nav.objects.filter(location="footer", route="/support").exists():
        order = (Nav.objects.filter(location="footer").aggregate(m=Max("display_order"))["m"] or 0) + 1
        Nav.objects.create(location="footer", label="Customer Support", route="/support", display_order=order, is_active=True)


def remove_support_links(apps, schema_editor):
    Nav = apps.get_model("tourist", "ManagedNavigationItem")
    Nav.objects.filter(route="/support", location__in=["navbar", "footer"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0066_card_grid_packages_blocks_and_homepage_sections"),
    ]

    operations = [
        migrations.RunPython(add_support_links, remove_support_links),
    ]
