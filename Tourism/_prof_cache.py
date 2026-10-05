"""Temporary: measure real request cost + cache effectiveness for /v1/models."""
import os
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import logging  # noqa: E402

logging.disable(logging.ERROR)

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402
from django.core.cache import cache  # noqa: E402


def timed(client, path, label):
    t0 = time.perf_counter()
    r = client.get(path, HTTP_ACCEPT="application/json")
    dt = time.perf_counter() - t0
    print(f"{label:34s} {dt:7.2f}s  status={r.status_code}  len={len(r.content)}")
    return r


c = Client()
print("--- warmup (imports + resolver build already done) ---")
timed(c, "/health", "GET /health (1st)")
timed(c, "/health", "GET /health (2nd)")

print("\n--- schema endpoint, repeated (cache_page should make 2nd+ fast) ---")
r1 = timed(c, "/api/v1/models/", "GET /api/v1/models/ (1st)")
print("   Vary:", r1.headers.get("Vary"), "| Cache-Control:", r1.headers.get("Cache-Control"))
r2 = timed(c, "/api/v1/models/", "GET /api/v1/models/ (2nd)")
r3 = timed(c, "/api/v1/models/", "GET /api/v1/models/ (3rd)")

print("\n--- different Accept header (new cache variant?) ---")
t0 = time.perf_counter()
c.get("/api/v1/models/", HTTP_ACCEPT="text/html")
print(f"  Accept:text/html -> {time.perf_counter() - t0:.2f}s")

print("\n--- with a Cookie header (Vary: Cookie variant) ---")
c2 = Client()
c2.cookies["sessionid"] = "abc123"
t0 = time.perf_counter()
c2.get("/api/v1/models/", HTTP_ACCEPT="application/json")
print(f"  Cookie variant   -> {time.perf_counter() - t0:.2f}s")

print("\nlocmem cache stats:", cache._cache.__class__.__name__)
try:
    print("cull:", cache._cull_frequency if hasattr(cache, "_cull_frequency") else "n/a")
except Exception:
    pass
print("cache get_count/misses via stats:", getattr(cache, "get_stats", lambda: "n/a")())
