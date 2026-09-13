from django.db import migrations

DASHBOARD_SECTIONS = [
    ("national-symbols", "cards", "National symbols", "Nepal's flag, emblem and identity at the top of the traveller dashboard."),
    ("hero", "heading", "Traveller dashboard", "Weather, safety, budget and AI picks for your Nepal trip."),
    ("weather-budget", "cards", "Weather and budget", "Current conditions and spending snapshot."),
    ("alerts", "cards", "Latest alerts", "Live hazard and travel alerts for your trip."),
    ("recommendations", "cards", "Recommended for you", "Personalised destination picks."),
    ("trending", "cards", "Trending Nepal destinations", "Popular places travellers are viewing now."),
    ("favorites", "cards", "Favorite places", "Destinations you have saved."),
    ("hotels", "cards", "Recommended hotels and stays", "Lodges matched to your trip."),
    ("culture", "text", "Nepal culture and local experiences", "Festivals, food and community highlights."),
    ("highlights", "text", "Why visit Nepal", "Signature reasons travellers choose Nepal."),
    ("safety", "text", "Safety status", "Full facility counts and live disaster data live on the Risk Analysis page."),
    ("budget-summary", "cards", "Budget summary", "Totals, spend and logged expense categories."),
    ("community-photos", "gallery", "Community photos", "Upload destination photos that can become official covers."),
]


def seed(apps, schema_editor):
    Page = apps.get_model("tourist", "ManagedPage")
    Section = apps.get_model("tourist", "ContentSection")
    page, _ = Page.objects.get_or_create(
        key="dashboard",
        defaults={
            "route": "/dashboard",
            "title": "Traveller Dashboard",
            "meta_description": "Traveller dashboard on the Digital Nepal Tourism Platform",
            "status": "published",
            "is_enabled": True,
        },
    )
    for order, (key, section_type, title, body) in enumerate(DASHBOARD_SECTIONS):
        defaults = {
            "title": title,
            "body": body,
            "display_order": order * 10,
            "status": "published",
            "is_visible": True,
        }
        if hasattr(Section, "section_type"):
            defaults["section_type"] = section_type
        Section.objects.get_or_create(page=page, key=key, defaults=defaults)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tourist", "0035_cms_seo_reusable_crop")]
    operations = [migrations.RunPython(seed, reverse)]
