"""Public SEO + health endpoints (§101–103, §112).

`robots.txt` and `sitemap.xml` are generated from live database records —
never a static snapshot — so a destination appears in the sitemap as soon as
it is published and disappears when it is unpublished. The sitemap is cached
briefly and the cache is invalidated by the admin lifecycle endpoints
(`invalidate_seo_cache`).

The health endpoint reports dependency status (application, database,
routing, weather, media storage) WITHOUT exposing credentials or internals.
"""
import logging
import os
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils.text import slugify
from django.views import View
from xml.sax.saxutils import escape

from .management.commands.normalize_district_names import NEPAL_DISTRICTS
from .models import Destination

logger = logging.getLogger(__name__)

SITEMAP_CACHE_KEY = "seo:sitemap:v1"
SITEMAP_TTL = 300  # bounded staleness; publish/unpublish invalidates eagerly

# Only routes that actually exist in the React app (App.jsx) — never invent URLs.
STATIC_PAGES = [
    ("/", "1.0", "daily"),
    ("/destinations", "0.9", "daily"),
    ("/districts", "0.8", "daily"),
    ("/emergency", "0.7", "monthly"),
    ("/navigation", "0.6", "monthly"),
    ("/itinerary", "0.5", "monthly"),
    ("/budget-estimator", "0.5", "monthly"),
    ("/about", "0.4", "yearly"),
    ("/contact", "0.4", "yearly"),
]


def public_base_url(request):
    """Canonical origin for absolute URLs (robots Sitemap line, sitemap locs)."""
    configured = (getattr(settings, "PUBLIC_SITE_URL", "") or "").strip()
    if configured:
        return configured.rstrip("/")
    return f"{request.scheme}://{request.get_host()}"


def invalidate_seo_cache():
    """Called by admin lifecycle endpoints so publish/unpublish is immediate."""
    cache.delete(SITEMAP_CACHE_KEY)


class RobotsTxtView(View):
    def get(self, request):
        base = public_base_url(request)
        lines = [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin",
            "Disallow: /staff",
            "Disallow: /portal",
            "Disallow: /profile",
            "Disallow: /dashboard",
            "Disallow: /my-bookings",
            "Disallow: /settings",
            "Disallow: /login",
            "Disallow: /register",
            "Disallow: /forgot-password",
            "Disallow: /api/",
            "",
            f"Sitemap: {base}/sitemap.xml",
            "",
        ]
        return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


class SitemapView(View):
    def get(self, request):
        xml = cache.get(SITEMAP_CACHE_KEY)
        if xml is None:
            xml = self._build(request)
            cache.set(SITEMAP_CACHE_KEY, xml, SITEMAP_TTL)
        return HttpResponse(xml, content_type="application/xml; charset=utf-8")

    def _build(self, request):
        base = public_base_url(request)
        urls = []

        def add(path, priority, changefreq, lastmod=None):
            loc = f"{base}{quote(path)}"
            entry = f"  <url>\n    <loc>{escape(loc)}</loc>\n"
            if lastmod:
                entry += f"    <lastmod>{lastmod}</lastmod>\n"
            entry += f"    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"
            urls.append(entry)

        for path, priority, changefreq in STATIC_PAGES:
            add(path, priority, changefreq)

        # All 77 districts (canonical list — same source as the public API).
        for province, names in NEPAL_DISTRICTS.items():
            for name in names:
                add(f"/districts/{slugify(name)}", "0.6", "weekly")

        # Published, search-visible destinations straight from the database.
        qs = (
            Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)
            .exclude(search_visible=False)
            .exclude(meta_robots="noindex")
            .only("slug", "updated_at")
            .order_by("slug")
        )
        for dest in qs.iterator():
            if not dest.slug:
                continue
            add(
                f"/destinations/{dest.slug}",
                "0.8",
                "weekly",
                dest.updated_at.date().isoformat() if dest.updated_at else None,
            )

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls)
            + "\n</urlset>\n"
        )


class HealthView(View):
    """GET /api/v1/health/ — dependency status, no secrets (§112)."""

    def get(self, request):
        checks = {"application": {"status": "ok"}}

        db_status = "ok"
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # pragma: no cover - depends on live DB state
            db_status = "error"
            logger.exception("Health check: database ping failed")
        checks["database"] = {"status": db_status, "engine": connection.vendor}

        routing_configured = bool((getattr(settings, "ROUTING_BASE_URL", "") or "").strip())
        checks["routing"] = {
            "status": "configured" if routing_configured else "fallback_only",
            "detail": "OSRM-compatible provider configured"
            if routing_configured
            else "no provider URL set; labelled local-graph fallback in use",
        }

        weather_configured = bool((getattr(settings, "OPENWEATHER_API_KEY", "") or "").strip())
        checks["weather"] = {"status": "configured" if weather_configured else "not_configured"}

        media_status = "ok"
        try:
            media_root = str(getattr(settings, "MEDIA_ROOT", ""))
            if not (media_root and os.path.isdir(media_root) and os.access(media_root, os.W_OK)):
                media_status = "unwritable"
        except Exception:  # pragma: no cover
            media_status = "error"
        checks["media_storage"] = {"status": media_status}

        overall = "ok" if db_status == "ok" and media_status == "ok" else "degraded"
        return JsonResponse(
            {"status": overall, "checks": checks},
            status=200 if overall == "ok" else 503,
        )
