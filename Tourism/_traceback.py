"""Temporary: get the real traceback behind the /travel-guides/ 500."""
import logging
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = ["*"]
logging.disable(logging.CRITICAL)

from tourist.models import TravelGuide  # noqa: E402

print("=== TravelGuide rows:", TravelGuide.objects.count())
print("=== published:", TravelGuide.objects.filter(is_published=True).count())

guide = TravelGuide.objects.filter(is_published=True).first()
print("\n=== first published guide:", guide, "| slug:", getattr(guide, "slug", None))

# Reproduce exactly what TravelGuideDetailView does.
from tourist.models import Destination  # noqa: E402

print("\n=== detail view query (the 500 source?) ===")
try:
    qs = TravelGuide.objects.select_related("destination").filter(
        slug=guide.slug,
        is_published=True,
        destination__is_active=True,
        destination__status=Destination.SubmissionStatus.APPROVED,
    )
    print("  matches:", qs.count())
except Exception:
    traceback.print_exc()

print("\n=== iterate guide.days (view touches this) ===")
try:
    days = list(guide.days.all())
    print("  days:", len(days))
    for day in days[:1]:
        for attr in (
            "day_number", "title", "description", "route", "travel_distance",
            "travel_time", "overnight_stay", "morning", "afternoon", "evening",
            "practical_notes",
        ):
            getattr(day, attr)
        print("  day attrs OK")
except Exception:
    traceback.print_exc()

print("\n=== LIST view body (TravelGuideListView) ===")
try:
    guides = TravelGuide.objects.filter(is_published=True).select_related("destination")
    out = []
    for g in guides:
        out.append({"slug": g.slug, "name": g.name, "destination": g.destination_id})
    print("  built", len(out), "rows")
except Exception:
    traceback.print_exc()

print("\n=== actual HTTP request, exceptions propagated ===")
from django.test import Client  # noqa: E402

settings.DEBUG_PROPAGATE_EXCEPTIONS = True
c = Client()
try:
    r = c.get("/api/v2/travel-guides/", HTTP_ACCEPT="application/json")
    print("  status:", r.status_code)
except Exception:
    traceback.print_exc()
