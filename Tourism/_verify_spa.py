"""Temporary: confirm the SPA and its assets are now served by Django."""
import logging
import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = ["*"]
settings.DEBUG_PROPAGATE_EXCEPTIONS = True
logging.disable(logging.CRITICAL)

from django.test import Client  # noqa: E402

c = Client()
J = {"HTTP_ACCEPT": "text/html"}

def body_of(resp):
    """spa_index returns a FileResponse (streaming), so .content is absent."""
    if hasattr(resp, "content"):
        return resp.content
    return b"".join(resp.streaming_content)


print("=== SPA routes (client-side paths must all return index.html) ===")
for path in ("/", "/destinations", "/login", "/signup", "/itinerary", "/search"):
    r = c.get(path, **J)
    body = body_of(r)
    is_html = b"<!doctype html" in body[:200].lower() or b"<html" in body[:400].lower()
    print(f"  {r.status_code}  {path:16s} {len(body):>7d}B  html={is_html}")

print("\n=== the bundle the SPA references ===")
r = c.get("/", **J)
html = body_of(r).decode("utf-8", "replace")
assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
print("  referenced assets:", assets[:4])
for a in assets[:3]:
    ra = c.get(a)
    print(f"    {ra.status_code}  {a}  {len(body_of(ra))}B")

print("\n=== favicon / pwa ===")
for p in ("/favicon.ico", "/favicon.svg", "/manifest.webmanifest"):
    rp = c.get(p)
    print(f"  {rp.status_code}  {p}")

print("\n=== API still routed correctly (not swallowed by the SPA) ===")
for p in ("/health", "/api/v2/destinations/", "/api/v1/travel-guides/"):
    rp = c.get(p, HTTP_ACCEPT="application/json")
    print(f"  {rp.status_code}  {p}  {len(rp.content)}B")
