"""Temporary: real traceback for the /travel-guides/ 500."""
import logging
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = ["*"]
settings.DEBUG_PROPAGATE_EXCEPTIONS = True
logging.disable(logging.CRITICAL)

from django.test import Client  # noqa: E402

c = Client()
try:
    r = c.get("/api/v1/travel-guides/", HTTP_ACCEPT="application/json")
    print("status:", r.status_code)
except Exception:
    traceback.print_exc()

print("\n=== data sanity for the list view ===")
from tourist.models import TravelGuide  # noqa: E402

qs = TravelGuide.objects.filter(is_published=True).select_related("destination")
print("  published guides:", qs.count())
print("  with destination :", qs.filter(destination__isnull=False).count())
print("  WITHOUT destination:", qs.filter(destination__isnull=True).count())
for g in qs.filter(destination__isnull=True)[:5]:
    print("    ->", g.slug, "| title:", g.title)
