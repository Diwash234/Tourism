"""End-to-end probe of the endpoints that were failing in production.

Runs against the real URLconf, middleware, throttles and serializers using
Django's test client, so anything that would 500 in production raises here too.

Usage:  python probe_endpoints.py
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402
from django.conf import settings  # noqa: E402

django.setup()

# The local .env runs with DEBUG=False, so SECURE_SSL_REDIRECT is on and the
# plain-HTTP test client gets 301'd before any view runs.
settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1", "*"]
settings.SECURE_SSL_REDIRECT = False

from django.test import Client  # noqa: E402

client = Client()

# Unique per run so repeat runs do not collide on the unique email index.
STAMP = str(int(time.time()))
ACCOUNT = {
    "email": f"probe.{STAMP}@example.com",
    "password": "Str0ng!Pass1",
    "password_confirm": "Str0ng!Pass1",
    "first_name": "Probe",
    "last_name": "User",
    "phone_number": "+9779812345678",
}

CHECKS = [
    ("register", "post", "/api/v1/auth/register/", ACCOUNT, (201,)),
    ("login", "post", "/api/v1/auth/login/",
     {"email": ACCOUNT["email"], "password": ACCOUNT["password"]}, (200,)),
    ("nearby", "get",
     "/api/v1/destinations/nearby/"
     "?latitude=27.332419&longitude=87.308972&radius_km=2000&page=1&page_size=12",
     None, (200,)),
    ("budget", "post", "/api/v1/ml/budget/",
     {"destination": "Pokhara", "travelers": 2, "days": 3, "style": "mid"}, (200,)),
    ("mood-recs", "get",
     "/api/v1/destinations/mood-recommendations/?mood=trekking&days=10&limit=6",
     None, (200,)),
    ("discover", "get", "/api/v1/discover-nepal/", None, (200,)),
    ("health", "get", "/api/v1/health/detailed/", None, (200,)),
]


def run(label, method, url, payload, expected):
    started = time.monotonic()
    try:
        if payload is None:
            response = getattr(client, method)(url)
        else:
            response = getattr(client, method)(
                url, data=json.dumps(payload), content_type="application/json"
            )
    except Exception as exc:  # noqa: BLE001 - the point is to surface the crash
        print(f"{label:<10} RAISED {type(exc).__name__}: {exc}")
        return False

    elapsed = time.monotonic() - started
    ok = response.status_code in expected
    body = response.content[:160].decode("utf-8", "replace").replace("\n", " ")
    print(f"{label:<10} {response.status_code} {elapsed:>6.2f}s "
          f"{'ok ' if ok else 'FAIL'} {body}")
    return ok


results = [run(*check) for check in CHECKS]

# The budget estimator is the one that silently degraded: it returned HTTP 200
# with a null total, which the UI renders as "unavailable".
budget_body = None
response = client.post(
    "/api/v1/ml/budget/",
    data=json.dumps({"destination": "Pokhara", "travelers": 2, "days": 3,
                     "style": "mid"}),
    content_type="application/json",
)
budget_body = response.json()
has_total = budget_body.get("total_budget_usd") is not None
print(f"{'budget':<10} total_budget_usd={budget_body.get('total_budget_usd')!r} "
      f"living_costs_available={budget_body.get('living_costs_available')} "
      f"{'ok' if has_total else 'FAIL (renders as unavailable)'}")
results.append(has_total)

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
