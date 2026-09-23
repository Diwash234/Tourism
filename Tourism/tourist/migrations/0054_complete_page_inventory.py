# Continuation brief: admins must be able to preview and manage EVERY page of
# the public/staff website. The frontend router exposes ~40 distinct pages but
# only 30 had ManagedPage rows, so the rest were invisible to the CMS (no
# title/SEO control, no editable intro, no preview entry).
#
# This migration registers every remaining real page (route + key + title +
# meta description) with one empty `intro` ContentSection each. The frontend's
# CMSPageIntro component renders NOTHING until an admin actually writes
# content, so public pages keep their exact current look by default — but the
# moment an admin edits a section or the page title/SEO fields, the change is
# persisted here and served through /config/public/ to the live site.
#
# Idempotent (get_or_create); routes mirror frontend/Tourism/src/App.jsx.
from django.db import migrations

# (route, key, title, meta_description)
NEW_PAGES = [
    ("/support", "customer-support", "Customer Support", "Get help with bookings, submissions and account questions on Nepal Yatra."),
    ("/privacy", "privacy-policy", "Privacy Policy", "How Nepal Yatra collects, uses and protects your personal data."),
    ("/terms", "terms-of-service", "Terms of Service", "The terms governing use of the Nepal Yatra platform."),
    ("/how-it-works", "how-it-works", "How Nepal Yatra Works", "A guide to planning, booking and exploring Nepal with the platform."),
    ("/thank-you", "thank-you", "Submission Received", "Confirmation and next steps after submitting a place or service."),
    ("/partner", "partner-desk", "Partner Desk", "Tourism businesses: list hotels, services and experiences on Nepal Yatra."),
    ("/collaborate", "collaborate", "Collaborate With Us", "Work with Nepal Yatra on data, content and community projects."),
    ("/profile", "profile", "My Profile", "Your traveller profile, stats and account details."),
    ("/personal-details", "personal-details", "Personal Details", "Travel documents and emergency details for you and your companions."),
    ("/hotels/search", "hotel-search", "Hotel Search", "Search hotels and lodges across Nepal by destination, price and facilities."),
    ("/nearby-places", "nearby-places", "Nearby Places", "Discover attractions and services near your current location."),
    ("/expenditure", "expenditure", "Travel Expenditure", "Track and review your Nepal travel spending history."),
    ("/my-submissions", "my-submissions", "My Submissions", "Track the places and services you submitted for review."),
    ("/notifications", "notifications", "Notifications", "Your alerts, submission updates and safety notifications."),
    ("/checkout", "checkout", "Booking Checkout", "Review and confirm your Nepal Yatra booking request."),
    ("/packages/:slug", "package-detail", "Package Detail", "Full details, itinerary and booking request for a travel package."),
    ("/trip", "shared-trip", "Shared Trip", "View a trip shared with you by family or travel companions."),
    ("/staff", "staff-desk", "Staff Operations Desk", "Capability-scoped workspace for Nepal Yatra staff reviewers."),
    ("/admin", "admin-console", "Admin Console", "Administrative overview of the Nepal Yatra platform."),
]

INTRO_COPY = {
    "customer-support": ("Support centre", "Answers and contact routes for travellers and partners."),
    "privacy-policy": ("Your privacy", "Plain-language summary of how your data is handled."),
    "terms-of-service": ("Platform terms", "What you can expect from Nepal Yatra, and what we expect from you."),
    "how-it-works": ("Getting started", "How search, planning, booking requests and verification fit together."),
    "thank-you": ("Thank you", "Your contribution helps keep the Nepal map accurate."),
    "partner-desk": ("For tourism businesses", "Reach travellers planning their Nepal trip."),
    "collaborate": ("Collaboration", "Data, content and community partnership opportunities."),
    "profile": ("Your journey", "Stats, badges and account controls in one place."),
    "personal-details": ("Travel documents", "Keep IDs and emergency details ready for you and your companions."),
    "hotel-search": ("Find your stay", "Compare verified hotels and lodges across Nepal."),
    "nearby-places": ("Around you", "Attractions and services ranked by real distance."),
    "expenditure": ("Spending history", "Every logged expense, categorised and totalled."),
    "my-submissions": ("Your contributions", "Review status of every place and service you submitted."),
    "notifications": ("Stay informed", "Submission updates, alerts and messages."),
    "checkout": ("Confirm your request", "Booking requests are reviewed before confirmation."),
    "package-detail": ("Package overview", "Itinerary, inclusions and booking details."),
    "shared-trip": ("Shared with you", "Live trip details shared by your travel group."),
    "staff-desk": ("Staff workspace", "Only records inside your assigned scope are shown."),
    "admin-console": ("Administration", "Platform-wide oversight and content control."),
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
        ("tourist", "0053_deduplicate_hotel_dataset_imports"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
