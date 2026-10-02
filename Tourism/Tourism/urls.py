from django.contrib import admin
from django.urls import path, include, re_path

from tourist import views_seo, views_auth
from tourist.health import DetailedHealthView
from tourist.dashboard import DashboardStatsView, PublicStatsView
from tourist.search import SearchAutocompleteView, FacetedSearchView
from django.conf import settings
from django.conf.urls.static import static
from .spa import spa_index
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # ==================================================================
    # API v1 (Current Stable Version)
    # ==================================================================
    # v1 is the current stable API. It will be deprecated in favor of v2.
    # Deprecation warning header is added via middleware.
    path("api/v1/admin-panel/", include("admin_panel.urls")),
    path("api/v1/navigation/", include("navigation.urls")),
    path("api/v1/", include("booking.urls")),
    path("api/v1/chatbot/", include("chatbot.urls")),
    path("api/v1/audit/", include("audit.urls")),
    path("api/v1/system/health/", include("system_health.urls")),
    path("api/v1/models/", SpectacularAPIView.as_view(), name="api-v1-models"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="api-v1-models"), name="api-v1-docs"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="api-v1-models"), name="api-v1-redoc"),
    path("api/v1/health/", views_seo.HealthView.as_view(), name="health-v1"),
    path("api/v1/health/detailed/", DetailedHealthView.as_view(), name="health-detailed-v1"),
    path("api/v1/dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats-v1"),
    path("api/v1/stats/", PublicStatsView.as_view(), name="public-stats-v1"),
    path("api/v1/search/autocomplete/", SearchAutocompleteView.as_view(), name="search-autocomplete-v1"),
    path("api/v1/search/faceted/", FacetedSearchView.as_view(), name="search-faceted-v1"),
    # Explicit auth routes are kept at the project URL layer as a deployment
    # compatibility guard. They resolve before the larger tourist include and
    # make the public login/logout contract unambiguous on Render.
    path("api/v1/auth/login/", views_auth.LoginView.as_view(), name="auth-login-project"),
    path("api/v1/auth/login", views_auth.LoginView.as_view(), name="auth-login-project-noslash"),
    path("api/v1/auth/logout/", views_auth.LogoutView.as_view(), name="auth-logout-project"),
    path("api/v1/auth/logout", views_auth.LogoutView.as_view(), name="auth-logout-project-noslash"),
    path("api/v1/", include("tourist.urls")),

    # ==================================================================
    # API v2 (Enhanced Version)
    # ==================================================================
    # v2 includes all v1 endpoints plus enhanced features:
    # - Improved pagination with cursor-based navigation
    # - Enhanced filtering and search capabilities
    # - Real-time WebSocket support
    # - AI-powered recommendations
    # - Advanced analytics endpoints
    # - Payment integration endpoints
    path("api/v2/admin-panel/", include("admin_panel.urls")),
    path("api/v2/navigation/", include("navigation.urls")),
    path("api/v2/", include("booking.urls")),
    path("api/v2/chatbot/", include("chatbot.urls")),
    path("api/v2/audit/", include("audit.urls")),
    path("api/v2/system/health/", include("system_health.urls")),
    path("api/v2/health/", views_seo.HealthView.as_view(), name="health-v2"),
    path("api/v2/health/detailed/", DetailedHealthView.as_view(), name="health-detailed-v2"),
    path("api/v2/dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats-v2"),
    path("api/v2/stats/", PublicStatsView.as_view(), name="public-stats-v2"),
    path("api/v2/search/autocomplete/", SearchAutocompleteView.as_view(), name="search-autocomplete-v2"),
    path("api/v2/search/faceted/", FacetedSearchView.as_view(), name="search-faceted-v2"),
    path("api/v2/", include("tourist.urls")),

    # ==================================================================
    # Public SEO surface (§101-103): generated from live DB records.
    # ==================================================================
    path("robots.txt", views_seo.RobotsTxtView.as_view(), name="robots-txt"),
    path("sitemap.xml", views_seo.SitemapView.as_view(), name="sitemap-xml"),

    # Deployment health check (§112) — root health endpoints
    path("health", views_seo.HealthView.as_view(), name="root-health"),
    path("health/", views_seo.HealthView.as_view(), name="root-health-slash"),

    # ==================================================================
    # Swagger / OpenAPI Documentation
    # ==================================================================
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Client-side routes of the built SPA (Docker image). Registered last and only
# when a build is installed, so API 404s and tests are unaffected.
if (settings.FRONTEND_DIST_DIR / "index.html").is_file():
    urlpatterns += [re_path(r"^(?!api/|admin/|static/|media/|ws/|assets/|images/|icons/|uploads/|favicon\\.ico$|manifest\\.webmanifest$|sw\\.js$)(?P<path>.*)$", spa_index, name="spa-index")]
