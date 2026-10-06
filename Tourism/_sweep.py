"""Temporary: sweep public endpoints to find what is empty or broken."""
import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = ["*"]
logging.disable(logging.CRITICAL)

from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402

print("=== DB sanity ===")
cur = connection.cursor()
for table in (
    "tourist_destination",
    "tourist_destinationimage",
    "tourist_travelguide",
    "tourist_user",
):
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table:32s} {cur.fetchone()[0]}")
    except Exception as exc:
        print(f"  {table:32s} ERROR {exc}")

print("\n=== is_unreadable_import column present & sane? ===")
try:
    cur.execute("PRAGMA table_info(tourist_destination)")
    cols = [r[1] for r in cur.fetchall()]
    print("  column exists:", "is_unreadable_import" in cols)
    if "is_unreadable_import" in cols:
        cur.execute(
            "SELECT is_unreadable_import, COUNT(*) FROM tourist_destination GROUP BY 1"
        )
        print("  flag distribution (flag, count):", cur.fetchall())
except Exception as exc:
    print("  ERROR", exc)

print("\n=== publicly_visible() ===")
from tourist.models import Destination  # noqa: E402

try:
    print("  count:", Destination.publicly_visible().count())
except Exception as exc:
    print("  ERROR", type(exc).__name__, exc)

print("\n=== endpoint sweep ===")
c = Client()
c.get("/health", HTTP_ACCEPT="application/json")
PATHS = [
    "/",
    "/api/v2/destinations/",
    "/api/v2/travel-guides/",
    "/api/v2/travel-guides/pokhara/",
    "/api/v2/curated-itineraries/",
    "/api/v2/city-itineraries/15-day/",
    "/api/v2/alerts/",
    "/api/v2/stats/",
    "/api/v2/search/autocomplete/?q=pok",
    "/api/v2/search/faceted/?q=pokhara",
    "/api/v2/emergency/contacts/",
    "/api/v2/admin-panel/",
    "/api/v1/destinations/",
]
for p in PATHS:
    try:
        r = c.get(p, HTTP_ACCEPT="application/json")
        body = r.content
        note = ""
        if r.status_code == 200 and p.endswith("/destinations/"):
            import json

            try:
                d = json.loads(body)
                n = d.get("count")
                if n is None:
                    n = len(d.get("results", []))
                note = f" count={n}"
            except Exception:
                pass
        print(f"  {r.status_code}  {p:44s} {len(body):>9d}B{note}")
    except Exception as exc:
        print(f"  EXC {p:44s} {type(exc).__name__}: {exc}")

print("\n=== SPA present? ===")
dist = settings.FRONTEND_DIST_DIR
print("  FRONTEND_DIST_DIR:", dist)
print("  index.html exists :", (dist / "index.html").is_file())
