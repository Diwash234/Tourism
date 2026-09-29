"""Give every page route of the site a CMS page record, and fix records that
were attached to the wrong route.

Before this migration 70 ManagedPage rows existed but 31 real page routes had
none (legal pages, Before You Travel, search/discover/decide, distances,
password reset, shared plans, staff workspace tabs, ...), so their title, SEO
and extra sections could not be edited in Admin -> CMS.

Three existing records pointed at the wrong route, so edits never reached the
page people actually see:

- ``privacy-policy`` was on ``/privacy`` and ``terms-of-service`` on
  ``/terms``. Both routes only redirect to ``/privacy-policy`` and
  ``/terms-of-service``.
- ``shared-trip`` ("View a trip shared with you by family...") was on
  ``/trip``, which is the booking-status lookup. The component that renders
  the ``shared-trip`` content is the family-shared view at
  ``/safety/shared/:token``.

The public config merges ``published_snapshot`` over the live fields
(including ``route``), so route fixes are applied to both.

Conventions follow 0054/0071/0073: idempotent ``get_or_create``, a hidden
draft ``intro`` section per new page (pages look unchanged until an admin
publishes content), and a published snapshot built like 0080. Titles and
descriptions reuse the wording the site already shows (``seoRoutes.js``,
page headers). Token, private and duplicate-alias pages are not
search-visible.
"""
from django.db import migrations

ROUTE_FIXES = [
    # key, old route, new route, search_visible (None = unchanged)
    ("privacy-policy", "/privacy", "/privacy-policy", None),
    ("terms-of-service", "/terms", "/terms-of-service", None),
    ("shared-trip", "/trip", "/safety/shared/:token", False),
]

BOOKING_STATUS = "Look up a booking request's status with the reference and email used at checkout."

NEW_PAGES = [
    # route, key, title, meta description, search_visible
    ("/cookie-policy", "cookie-policy", "Cookie Policy",
     "The cookies and browser storage Nepal Yatra uses, what each one is for, and how to clear them.", True),
    ("/data-deletion", "data-deletion", "Delete your account and data",
     "How to delete your Nepal Yatra account, what is removed, and what is kept for legal or safety reasons.", True),
    ("/unsubscribe", "unsubscribe", "Unsubscribe from travel notes",
     "Stop receiving Nepal Yatra travel-note emails.", True),
    ("/before-you-travel", "before-you-travel", "Before you travel: visas, permits and fees",
     "Nepal visa, TIMS, restricted-area permit, national park and heritage fees, altitude safety and insurance notes, "
     "transcribed from official sources.", True),
    ("/distances", "distances", "Distances and directions",
     "Road and straight-line distances between places in Nepal, labelled by how each distance was measured.", True),
    ("/search", "search", "Search",
     "Search Nepal destinations, districts, hotels, services and travel rules in one place.", True),
    ("/discover", "discover", "Find places by activity and season",
     "Filter Nepal destinations by activity, effort, altitude, season, official fees, accessibility notes and "
     "distance from where you start.", True),
    ("/decide", "decide", "Help me decide",
     "Compare two to four Nepal destinations for your month: season fit, distance, altitude, official fees, "
     "nearest hospital and hotels, with sources.", True),
    ("/trip", "trip-status", "Trip request status", BOOKING_STATUS, True),
    ("/trip/:reference", "trip-status-reference", "Trip request status", BOOKING_STATUS, False),
    ("/plans/shared/:token", "shared-plan", "Shared trip plan", "A read-only trip plan shared by its owner.", False),
    ("/verify-email", "auth-verify-email", "Verify email",
     "Confirm your email address to finish creating your Nepal Yatra account.", False),
    ("/reset-password", "auth-reset-password", "Choose a new password",
     "Set a new password for your Nepal Yatra account using the link from your reset email.", False),
    # Aliases of pages that already have records: separate records so each URL
    # can get its own title or sections; they fall back to the main page's
    # content until an admin adds sections here.
    ("/login/user", "auth-login-user", "Sign In",
     "Sign in to plan trips, save favourites and track bookings on Nepal Yatra.", False),
    ("/destinations/compare", "compare-destinations", "Compare Destinations",
     "Compare up to four Nepal destinations side by side using the facts on record, with missing values clearly marked.",
     False),
    ("/safety", "safety", "Family Safety",
     "Share your trip status with family and trusted contacts while you travel in Nepal.", False),
]

# Staff workspace tabs (names as shown in StaffDashboard.jsx).
STAFF_TABS = {
    "destinations": "Destination Queue", "images": "Image Review", "budget": "Budget Surveys",
    "safety": "Safety Reports", "reviews": "Review Queue", "hotels": "Assigned Hotels",
    "restaurants": "Restaurant Queue", "transportation": "Transport Routes", "travel-plans": "Travel Plans",
    "content": "Content Drafts", "feedback": "Feedback Queue",
}
for _slug, _name in STAFF_TABS.items():
    NEW_PAGES.append((f"/staff/{_slug}", f"staff-{_slug}", f"Staff: {_name}",
                      f"Staff workspace: {_name.lower()}. Only records in your assigned scope are shown.", False))

SNAPSHOT_FIELDS = ("key", "route", "title", "meta_description", "seo_title", "og_image_url",
                   "search_visible", "is_enabled")


def _snapshot(page):
    return {field: getattr(page, field) for field in SNAPSHOT_FIELDS}


def forwards(apps, schema_editor):
    Page = apps.get_model("tourist", "ManagedPage")
    Section = apps.get_model("tourist", "ContentSection")

    for key, old_route, new_route, visible in ROUTE_FIXES:
        page = Page.objects.filter(key=key, route=old_route).first()
        if not page or Page.objects.filter(route=new_route).exclude(pk=page.pk).exists():
            continue
        page.route = new_route
        fields = ["route"]
        if visible is not None:
            page.search_visible = visible
            fields.append("search_visible")
        if isinstance(page.published_snapshot, dict) and page.published_snapshot:
            snap = dict(page.published_snapshot)
            snap["route"] = new_route
            if visible is not None:
                snap["search_visible"] = visible
            page.published_snapshot = snap
            fields.append("published_snapshot")
        page.save(update_fields=fields)

    for route, key, title, meta, visible in NEW_PAGES:
        if Page.objects.filter(route=route).exclude(key=key).exists():
            continue  # an editor already created a page for this route
        page, created = Page.objects.get_or_create(key=key, defaults={
            "route": route, "title": title, "meta_description": meta[:320],
            "status": "published", "is_enabled": True, "search_visible": visible,
        })
        if created:
            page.published_snapshot = _snapshot(page)
            page.save(update_fields=["published_snapshot"])
        defaults = {"title": title, "body": "", "display_order": 0, "status": "draft", "is_visible": False}
        if hasattr(Section, "section_type"):
            defaults["section_type"] = "text"
        Section.objects.get_or_create(page=page, key="intro", defaults=defaults)


class Migration(migrations.Migration):
    dependencies = [("tourist", "0090_publish_page_meta_descriptions")]
    # Reverse is a no-op: pages may have been edited by then, never delete them.
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
