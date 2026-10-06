"""Temporary: invoke the view's logic directly, past the exception handler."""
import logging
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

logging.disable(logging.CRITICAL)

from django.test import RequestFactory  # noqa: E402

from tourist.models import TravelGuide  # noqa: E402
from tourist.views import TravelGuideListView  # noqa: E402

rf = RequestFactory()
request = rf.get("/api/v1/travel-guides/", HTTP_ACCEPT="application/json")

view = TravelGuideListView.as_view()
try:
    resp = view(request)
    print("status:", resp.status_code)
except Exception:
    print("=== LIST view traceback ===")
    traceback.print_exc()

print("\n=== step through it manually ===")
try:
    guides = TravelGuide.objects.filter(is_published=True).select_related("destination")
    rows = []
    for g in guides:
        rows.append(
            {
                "slug": g.slug,
                "title": g.title,
                "days_count": g.days_count,
                "destination_name": g.destination.name,
                "destination_slug": g.destination.slug,
            }
        )
    print("  built", len(rows), "rows OK")
except Exception:
    traceback.print_exc()

print("\n=== DETAIL view, first slug ===")
slug = TravelGuide.objects.filter(is_published=True).values_list("slug", flat=True).first()
print("  slug:", slug)
request2 = rf.get(f"/api/v1/travel-guides/{slug}/", HTTP_ACCEPT="application/json")
try:
    resp2 = TravelGuideDetailView.as_view()(request2, slug=slug)
    print("  status:", resp2.status_code)
except Exception:
    print("=== DETAIL traceback ===")
    traceback.print_exc()
