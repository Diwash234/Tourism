"""Stop showing the CMS catalogue's placeholder copy to the public.

Migration 0034 seeded every managed page with a *published, visible*
"page-intro" section ("This section is managed from the Admin Content
Publishing Studio.") and six pages with a "featured-content" section
("Configure featured cards, media and calls to action here."). That is
instructions for administrators, not content, yet it rendered above the real
page on /emergency, /hotels, /destinations, the home page, etc. and pushed
the national hotlines below the fold on the emergency page.

This migration moves only *untouched* seeded placeholders back to draft and
hidden: the key, title and body must still equal the seeded defaults, both in
the live fields and in any published snapshot. Anything an administrator has
edited is left exactly as it is. The drafts stay in the Content Publishing
Studio so an admin can write real copy and publish it.
"""

from django.db import migrations

PLACEHOLDERS = {
    "page-intro": "This section is managed from the Admin Content Publishing Studio.",
    "featured-content": "Configure featured cards, media and calls to action here.",
}


# Page titles exactly as 0034 seeded them (pages may have been renamed since).
SEEDED_PAGE_TITLES = {
    "home": "Discover Nepal", "dashboard": "Traveller Dashboard", "destinations": "Destinations",
    "gallery": "Visual Gallery", "compare": "Compare Destinations", "discover-nepal": "Discover Nepal",
    "packages": "Travel Packages", "explore-map": "Explore by Province",
    "recommendation": "AI Recommendations", "navigation": "Route Navigation",
    "hotels": "Hotels and Lodges", "budget-estimator": "Budget Estimator",
    "trip-planner": "Trip Planner", "itinerary": "Itinerary Planner", "risk-alerts": "Risk Alerts",
    "family-safety": "Family Safety", "emergency": "Emergency Hub", "phrasebook": "Nepal Phrasebook",
    "translation": "Live Translation", "chatbot": "Himal AI Assistant", "favorites": "Saved Favorites",
    "bookings": "My Bookings", "history": "Visit History", "about": "About Us",
    "contact": "Contact Us", "settings": "Settings", "submit-place": "Submit a Place",
    "submit-service": "Submit a Tourism Service",
}


def _seeded_title(key, page_title):
    return page_title if key == "page-intro" else f"Featured {page_title}"


def _seeded_subtitle(key, page_title):
    if key == "page-intro":
        return f"Explore {page_title.lower()} with verified tourism information."
    return ""


def _is_untouched(section):
    body = PLACEHOLDERS.get(section.key)
    if body is None or (section.body or "").strip() != body:
        return False
    # Conservative: the title must still be the seeded one (page title, or
    # "Featured <page title>"). If an admin touched it, leave the section alone.
    candidates = {section.page.title or "", SEEDED_PAGE_TITLES.get(section.page.key, "")} - {""}
    if not any(
        (section.title or "") == _seeded_title(section.key, t)
        and (section.subtitle or "") == _seeded_subtitle(section.key, t)
        for t in candidates
    ):
        return False
    if section.image_url or section.cta_text or section.cta_url:
        return False
    snap = section.published_snapshot if isinstance(section.published_snapshot, dict) else None
    if snap and snap.get("body") not in (None, "", body):
        return False
    return not section.blocks.exists()


def unpublish_placeholders(apps, schema_editor):
    ContentSection = apps.get_model("tourist", "ContentSection")
    qs = ContentSection.objects.select_related("page").filter(
        key__in=list(PLACEHOLDERS), body__in=list(PLACEHOLDERS.values())
    )
    for section in qs:
        if not _is_untouched(section):
            continue
        section.status = "draft"
        section.is_visible = False
        fields = ["status", "is_visible"]
        if isinstance(section.published_snapshot, dict) and section.published_snapshot:
            snap = dict(section.published_snapshot)
            snap["is_visible"] = False
            section.published_snapshot = snap
            fields.append("published_snapshot")
        section.save(update_fields=fields)


def noop(apps, schema_editor):
    # Never re-publish placeholder copy on reverse.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0080_backfill_managed_page_snapshots"),
    ]

    operations = [
        migrations.RunPython(unpublish_placeholders, noop),
    ]
