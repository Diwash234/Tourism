# Admin CMS coverage completion: every remaining PUBLIC page of the site gets
# a ManagedPage row so title/SEO/intro/sections are admin-controlled. Pages
# added here: the 77-district pages, guides, tourism jobs, the four auth
# screens and the 404. Internal role workspaces (guide portal, local
# dashboard, admin sub-routes) intentionally stay out — they are tools, not
# public pages.
#
# Idempotent (get_or_create), mirrors 0054. CMSPageIntro renders nothing
# until an admin writes content, so every page keeps its current look.
from django.db import migrations

NEW_PAGES = [
    ("/districts", "districts", "Districts of Nepal", "Browse all 77 districts of Nepal with verified places, safety and travel facts."),
    ("/districts/:slug", "district-detail", "District Profile", "District profile: places by category, hospitals, safety and nearby districts."),
    ("/guides", "guides", "Local Guides", "Find verified local guides for treks, tours and cultural experiences in Nepal."),
    ("/tourism-jobs", "tourism-jobs", "Tourism Jobs", "Job openings across Nepal's tourism sector — hotels, trekking and services."),
    ("/login", "auth-login", "Sign In", "Sign in to plan trips, save favourites and track bookings on Nepal Yatra."),
    ("/register", "auth-register", "Create Account", "Create your Nepal Yatra traveller account."),
    ("/forgot-password", "auth-recovery", "Reset Password", "Reset your Nepal Yatra password securely."),
    ("/verify-phone", "auth-verify", "Verify Phone", "Verify your phone number to activate safety and booking features."),
    ("*", "not-found", "Page Not Found", "That page does not exist — return to exploring Nepal."),
]

INTRO_COPY = {
    "districts": ("77 districts", "Every district with its verified places and practical travel facts."),
    "district-detail": ("District profile", "Places by category, hospitals, police and the nearest districts."),
    "guides": ("Local expertise", "Verified guides for treks, culture and off-the-beaten-path Nepal."),
    "tourism-jobs": ("Work in tourism", "Current openings from hotels, trekking companies and services."),
    "auth-login": ("Welcome back", "Sign in to continue planning your Nepal trip."),
    "auth-register": ("Join Nepal Yatra", "One account for planning, booking requests and safety tools."),
    "auth-recovery": ("Password reset", "We will send you a secure reset link."),
    "auth-verify": ("Phone verification", "One last step to activate safety features."),
    "not-found": ("Lost the trail?", "The page you were looking for has moved or never existed."),
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
            "status": "draft",  # invisible until an admin reviews/publishes it
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
        ("tourist", "0070_seed_fare_card"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
