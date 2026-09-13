"""Adds card_grid + packages block types and seeds two draft homepage
sections (Travel Planning tools, Featured Travel Packages) so the homepage
editor has them ready. They are DRAFTS: the public homepage is unchanged
until an admin reviews and publishes them (CMS prompt §8/§9/§23)."""
from django.db import migrations, models


def seed_homepage_sections(apps, schema_editor):
    ManagedPage = apps.get_model("tourist", "ManagedPage")
    ContentSection = apps.get_model("tourist", "ContentSection")
    ContentBlock = apps.get_model("tourist", "ContentBlock")
    home = ManagedPage.objects.filter(route="/").first()
    if not home:
        return
    tp, created = ContentSection.objects.get_or_create(
        page=home, key="travel-planning",
        defaults={
            "title": "Everything You Need to Plan Nepal",
            "subtitle": "PLAN YOUR TRIP",
            "body": "Build your perfect Nepal journey — itinerary, budget, stays and safety in one place.",
            "section_type": "cards", "layout_variant": "cards",
            "display_order": 15, "is_visible": True, "status": "draft",
        })
    if created:
        ContentBlock.objects.create(
            section=tp, block_type="card_grid", title="Planning tools", position=1,
            data={"items": [
                {"emoji": "🗺️", "title": "Itinerary", "description": "Build your Nepal itinerary.", "url": "/travel-planning"},
                {"emoji": "💰", "title": "Budget", "description": "Estimate your travel costs.", "url": "/budget-estimator"},
                {"emoji": "🏨", "title": "Hotels", "description": "Find suitable accommodation.", "url": "/hotels"},
                {"emoji": "⚠️", "title": "Risk Alerts", "description": "Understand travel risks and important information.", "url": "/safety"},
            ]})
    fp, created = ContentSection.objects.get_or_create(
        page=home, key="featured-packages",
        defaults={
            "title": "Explore Nepal's Best Experiences",
            "subtitle": "FEATURED EXPERIENCES",
            "body": "Discover hand-picked journeys across Nepal — live from the marketplace desk.",
            "cta_text": "Browse all packages", "cta_url": "/packages",
            "section_type": "cards", "layout_variant": "cards",
            "display_order": 25, "is_visible": True, "status": "draft",
        })
    if created:
        ContentBlock.objects.create(
            section=fp, block_type="packages", title="Featured packages", position=1,
            data={"limit": 6})


def unseed(apps, schema_editor):
    ContentSection = apps.get_model("tourist", "ContentSection")
    ContentSection.objects.filter(key__in=["travel-planning", "featured-packages"]).delete()


class Migration(migrations.Migration):
    dependencies = [("tourist", "0065_backfill_published_snapshots")]
    operations = [
        migrations.AlterField(
            model_name="contentblock", name="block_type",
            field=models.CharField(choices=[
                ("heading", "Heading"), ("subheading", "Subheading"), ("rich_text", "Rich Text"),
                ("image", "Image"), ("gallery", "Gallery"), ("button", "Button"),
                ("table", "Table"), ("video", "Video / Iframe"), ("map", "Map"),
                ("destination_grid", "Destination Grid"), ("hotel_grid", "Hotel Grid"),
                ("restaurant_grid", "Restaurant Grid"), ("statistics", "Statistics"),
                ("list", "List"), ("quote", "Quote"), ("alert", "Alert / Callout"),
                ("divider", "Divider"), ("html", "Custom Safe HTML"),
                ("card_grid", "Card Grid"), ("packages", "Travel Packages Grid"),
            ], default="rich_text", max_length=50),
        ),
        migrations.RunPython(seed_homepage_sections, unseed),
    ]
