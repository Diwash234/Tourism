from django.contrib import admin
from django.urls import path, include

from tourist import views_seo
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/admin-panel/", include("admin_panel.urls")),
    path("api/v1/navigation/", include("navigation.urls")),
    path("api/v1/", include("booking.urls")),
    path("api/v1/chatbot/", include("chatbot.urls")),
    path("api/v1/audit/", include("audit.urls")),                # audit logs / errors / health samples
    path("api/v1/system/health/", include("system_health.urls")),  # live health checks
    # path("api/v1/safety/", include("safety.urls")),
    # path("api/v1/", include("translation.urls")),
    # path("api/v1/", include("media_app.urls")),
    # Public SEO surface (§101-103): generated from live DB records.
    path("robots.txt", views_seo.RobotsTxtView.as_view(), name="robots-txt"),
    path("sitemap.xml", views_seo.SitemapView.as_view(), name="sitemap-xml"),
    # Deployment health check (§112) — root and api/v1/ health endpoints
    path("health", views_seo.HealthView.as_view(), name="root-health"),
    path("health/", views_seo.HealthView.as_view(), name="root-health-slash"),
    path("api/v1/health/", views_seo.HealthView.as_view(), name="health"),
    path("api/v1/", include("tourist.urls")),

    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
