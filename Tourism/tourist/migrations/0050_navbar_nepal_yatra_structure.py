# Data migration: enforce the Nepal Yatra navbar structure everywhere
# (runtime DBs AND fresh installs built from migrations).
#   Tops: Home, Explore, Plan a Trip, Emergency Services, About
#   Plan a Trip children: Destinations, Itinerary, Budget Estimator, Hotels, Risk Alerts
#   Explore children: Recommended, Gallery, Compare Places, Explore by Province
#   Emergency Services children: Family Safety, Emergency / SOS
# Idempotent: safe to run against a DB that already has this shape.
from django.db import migrations


def forwards(apps, schema_editor):
    N = apps.get_model("tourist", "ManagedNavigationItem")

    def top(label, route, order, rename_from=()):
        item = N.objects.filter(location="navbar", parent__isnull=True, label=label).first()
        if not item and rename_from:
            item = (
                N.objects.filter(location="navbar", parent__isnull=True, label__in=list(rename_from))
                .order_by("id")
                .first()
            )
            if item:
                item.label = label
        if not item:
            item = N(location="navbar", parent=None, label=label)
        item.route = route
        item.display_order = order
        item.is_active = True
        item.save()
        return item

    home = top("Home", "/", 0)
    explore = top("Explore", "/destinations", 1)
    plan = top("Plan a Trip", "/trip-planner", 2, rename_from=("Travel Planning", "Plan"))
    emerg = top("Emergency Services", "/emergency", 3, rename_from=("Safety", "Travel Safely"))
    about = top("About", "/about", 4)

    keep = {home.id, explore.id, plan.id, emerg.id, about.id}
    N.objects.filter(location="navbar", parent__isnull=True).exclude(id__in=keep).update(is_active=False)

    def child(parent, label, route, order):
        item = N.objects.filter(location="navbar", parent=parent, label=label).first()
        if not item:
            # Adopt an existing navbar item with this label that sits under the
            # wrong parent (or is an orphaned duplicate top) instead of
            # creating yet another row.
            item = N.objects.filter(location="navbar", label=label).exclude(parent=parent).order_by("id").first()
        if not item:
            item = N(location="navbar", label=label)
        item.parent = parent
        item.route = route
        item.display_order = order
        item.is_active = True
        item.save()

    child(explore, "Recommended", "/recommendation", 0)
    child(explore, "Gallery", "/gallery", 1)
    child(explore, "Compare Places", "/compare", 2)
    child(explore, "Explore by Province", "/explore-map", 3)

    child(plan, "Destinations", "/destinations", 0)
    child(plan, "Itinerary", "/itinerary", 1)
    child(plan, "Budget Estimator", "/budget-estimator", 2)
    child(plan, "Hotels", "/hotels", 3)
    child(plan, "Risk Alerts", "/risk-alerts", 4)

    child(emerg, "Family Safety", "/family-safety", 0)
    child(emerg, "Emergency / SOS", "/emergency", 1)


def backwards(apps, schema_editor):
    # Structure change is additive/idempotent; no destructive reversal.
    pass


class Migration(migrations.Migration):
    dependencies = [("tourist", "0049_seed_default_hero_slides")]
    operations = [migrations.RunPython(forwards, backwards)]
