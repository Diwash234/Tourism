from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


HOME_SECTIONS = [
    ("hero", "heading", "Explore Nepal", "Discover destinations across all 7 provinces."),
    ("features", "cards", "Why travel with Nepal Portal", "Verified places, budgets, safety and navigation."),
    ("featured", "cards", "Featured Nepal destinations", "Handpicked wonders from the live catalogue."),
    ("case-studies", "cards", "Expedition blueprints", "Real itineraries travellers follow."),
    ("highlights", "text", "Why visit Nepal", "Signature reasons travellers choose Nepal."),
    ("symbols", "cards", "National symbols", "Nepal's identity at a glance."),
    ("culture", "text", "Culture and local experiences", "Festivals, food and community highlights."),
    ("provinces", "cards", "Explore by province", "Regional attractions from east to west."),
    ("marquee", "marquee", "Seven provinces of Nepal", "Koshi · Madhesh · Bagmati · Gandaki · Lumbini · Karnali · Sudurpashchim"),
    ("testimonials", "cards", "Traveller stories", "Verified experiences from the road."),
    ("faq", "faq", "Frequently asked questions", "Practical answers before you travel."),
    ("cta", "cta", "Start planning", "Open destinations or estimate a budget."),
]

DESTINATION_LIST_SECTIONS = [
    ("intro", "heading", "Explore Nepal", "Temples, lakes, trails and heritage across seven provinces."),
    ("search", "text", "Find a place", "Search by name, district or category."),
    ("featured", "cards", "Featured places", "Live catalogue results."),
]

DESTINATION_DETAIL_SECTIONS = [
    ("hero", "heading", "Destination profile", "Photos, routes, budget and safety for this place."),
    ("about", "text", "About this place", "Managed overview for travellers."),
    ("gallery", "gallery", "Photos", "Verified destination media."),
    ("video", "video", "Community video", "Traveller clips up to 25 MB."),
    ("map", "map", "Map", "Location on the Nepal map."),
]

FOOTER_SECTIONS = [
    ("symbols", "cards", "National symbols", "Discover Nepal — Beyond Everest"),
    ("explore", "text", "Explore", "Destinations, recommendations, budget and alerts."),
    ("provinces", "cards", "Provinces", "Jump to a province city."),
    ("company", "text", "Company", "About, contact and emergency."),
    ("contact", "text", "Contact", "Pokhara, Nepal"),
    ("tagline", "text", "Footer note", "Discover destinations, plan budgets, and travel safely through Nepal."),
]


def seed(apps, schema_editor):
    Page = apps.get_model("tourist", "ManagedPage")
    Section = apps.get_model("tourist", "ContentSection")
    Nav = apps.get_model("tourist", "ManagedNavigationItem")
    pages = {
        "home": ("/", "Discover Nepal"),
        "destinations": ("/destinations", "Destinations"),
        "destination-detail": ("/destinations/:slug", "Destination detail"),
        "footer": ("/footer", "Site footer"),
    }
    catalogs = {
        "home": HOME_SECTIONS,
        "destinations": DESTINATION_LIST_SECTIONS,
        "destination-detail": DESTINATION_DETAIL_SECTIONS,
        "footer": FOOTER_SECTIONS,
    }
    for key, (route, title) in pages.items():
        page, _ = Page.objects.get_or_create(
            key=key,
            defaults={"route": route, "title": title, "status": "published", "is_enabled": True,
                      "meta_description": f"{title} on the Digital Nepal Tourism Platform"},
        )
        for order, (section_key, section_type, section_title, body) in enumerate(catalogs[key]):
            defaults = {
                "title": section_title, "body": body, "display_order": order * 10,
                "status": "published", "is_visible": True, "section_type": section_type,
            }
            Section.objects.get_or_create(page=page, key=section_key, defaults=defaults)
    footer_links = [
        ("Destinations", "/destinations"), ("Recommendations", "/recommendation"),
        ("Budget Estimator", "/budget-estimator"), ("Risk Alerts", "/risk-alerts"),
        ("About Us", "/about"), ("Contact", "/contact"), ("Emergency", "/emergency"),
    ]
    for order, (label, route) in enumerate(footer_links):
        Nav.objects.get_or_create(
            location="footer", route=route,
            defaults={"label": label, "display_order": order, "is_active": True},
        )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tourist", "0036_dashboard_cms_sections"),
    ]

    operations = [
        migrations.AddField(
            model_name="destinationvideo",
            name="caption",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="destinationvideo",
            name="uploaded_by",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=models.deletion.SET_NULL,
                related_name="uploaded_videos", to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="destinationvideo",
            name="verification_status",
            field=models.CharField(
                choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="approved", max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="destinationvideo",
            name="video_file",
            field=models.FileField(blank=True, null=True, upload_to="destinations/videos/"),
        ),
        migrations.AlterField(
            model_name="destinationvideo",
            name="video_url",
            field=models.URLField(blank=True, help_text="YouTube/Vimeo link or hosted video URL"),
        ),
        migrations.AlterField(
            model_name="contentsection",
            name="section_type",
            field=models.CharField(
                choices=[
                    ("text", "Text"), ("heading", "Heading"), ("image", "Image"), ("gallery", "Gallery"),
                    ("cards", "Cards"), ("faq", "FAQ"), ("cta", "Call to action"), ("map", "Map"),
                    ("video", "Video"), ("audio", "Audio"), ("marquee", "Marquee"),
                    ("animation", "Animation"), ("media", "Media"),
                ],
                default="text", max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="contentsection",
            name="layout_variant",
            field=models.CharField(
                choices=[
                    ("default", "Default"), ("compact", "Compact"), ("wide", "Wide"),
                    ("cards", "Cards"), ("hero", "Hero"), ("split", "Split"),
                ],
                default="default", max_length=30,
            ),
        ),
        migrations.RunPython(seed, reverse),
    ]
