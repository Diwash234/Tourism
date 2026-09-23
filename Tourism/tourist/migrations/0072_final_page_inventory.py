# Final CMS page inventory: registers the last content-bearing screens —
# the three portal logins, guide workspace pages, local dashboard and the
# three admin tool pages. After this migration every route in App.jsx that
# renders page content has a ManagedPage (only transient redirect screens
# such as /trip-planner and /auth/callback/:provider are excluded — they
# have no content area by design).
#
# Idempotent (get_or_create), mirrors 0054/0071.
from django.db import migrations

NEW_PAGES = [
    ("/portal", "portal-login", "Portal Sign In", "Staff and partner portal sign in for Nepal Yatra."),
    ("/staff/login", "staff-login", "Staff Sign In", "Sign in to the Nepal Yatra staff workspace."),
    ("/admin/login", "admin-login", "Admin Sign In", "Administrative sign in for Nepal Yatra."),
    ("/guide-portal", "guide-portal", "Guide Portal", "Workspace for verified local guides: profile, availability and trips."),
    ("/guide-bookings", "guide-bookings", "Guide Bookings", "Booking requests received by guides and their status."),
    ("/local/dashboard", "local-dashboard", "Local Dashboard", "Local operator dashboard for listings and community content."),
    ("/admin/diagnostics", "admin-diagnostics", "Platform Diagnostics", "System health, queues and service diagnostics."),
    ("/admin/hotel-assignments", "admin-hotel-assignments", "Hotel Assignments", "Assign and review hotel records across staff."),
    ("/admin/tasks", "admin-tasks", "Admin Tasks", "Operational task board for administrators."),
    ("/hotels/:hotelId/book", "hotel-booking", "Book a Hotel", "Request a hotel or lodge booking on Nepal Yatra."),
]

INTRO_COPY = {
    "portal-login": ("Portal access", "One entrance for staff and partner tools."),
    "staff-login": ("Staff access", "Sign in to review and verify tourism records."),
    "admin-login": ("Administration", "Platform oversight and content control."),
    "guide-portal": ("Guide workspace", "Manage your profile, availability and trips."),
    "guide-bookings": ("Your bookings", "Every booking request in one queue."),
    "local-dashboard": ("Local operations", "Listings and community content tools."),
    "admin-diagnostics": ("Diagnostics", "Service health and queue status."),
    "admin-hotel-assignments": ("Assignments", "Hotel records mapped to reviewers."),
    "admin-tasks": ("Task board", "Operational tasks and their progress."),
    "hotel-booking": ("Your stay", "Review the details and send your booking request."),
}


def seed(apps, schema_editor):
    Page = apps.get_model("tourist", "ManagedPage")
    Section = apps.get_model("tourist", "ContentSection")
    for route, key, title, meta in NEW_PAGES:
        page, created = Page.objects.get_or_create(
            key=key,
            defaults={
                "route": route,
                "title": title,
                "meta_description": meta,
                "status": "published",
                "is_enabled": True,
            },
        )
        if not created and not page.route:
            page.route = route
            page.save(update_fields=["route"])
        intro_title, intro_body = INTRO_COPY.get(key, (title, meta))
        defaults = {
            "title": intro_title,
            "body": intro_body,
            "display_order": 0,
            "status": "draft",
            "is_visible": False,
        }
        if hasattr(Section, "section_type"):
            defaults["section_type"] = "text"
        Section.objects.get_or_create(page=page, key="intro", defaults=defaults)


def unseed(apps, schema_editor):
    Page = apps.get_model("tourist", "ManagedPage")
    Page.objects.filter(key__in=[key for _, key, _, _ in NEW_PAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0071_complete_public_page_inventory"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
