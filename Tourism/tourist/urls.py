from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from . import views, views_auth, views_ml, views_compat, views_osm

router = DefaultRouter()
router.register("languages", views.LanguageViewSet, basename="language")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("destinations", views.DestinationViewSet, basename="destination")
router.register("destination-images", views.DestinationImageViewSet, basename="destination-image")
router.register("destination-videos", views.DestinationVideoViewSet, basename="destination-video")
router.register("reviews", views.ReviewViewSet, basename="review")
router.register("ratings", views.RatingViewSet, basename="rating")
router.register("favorites", views.FavoriteViewSet, basename="favorite")
router.register("history", views.VisitHistoryViewSet, basename="history")
router.register("budgets", views.BudgetViewSet, basename="budget")
router.register("alerts", views.AlertViewSet, basename="alert")
router.register("emergency-contacts", views.EmergencyContactViewSet, basename="emergency-contact")
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("device-tokens", views.DeviceTokenViewSet, basename="device-token")
router.register("hotels", views.HotelViewSet, basename="hotel")

auth_urlpatterns = [
    path("auth/register/", views_auth.RegisterView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="auth-token-verify"),
    path("auth/logout/", views_auth.LogoutView.as_view(), name="auth-logout"),
    path("auth/verify-email/", views_auth.VerifyEmailView.as_view(), name="auth-verify-email"),
    path("auth/resend-verification/", views_auth.ResendVerificationEmailView.as_view(), name="auth-resend-verification"),
    path("auth/forgot-password/", views_auth.ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password/", views_auth.ResetPasswordView.as_view(), name="auth-reset-password"),
    path("auth/change-password/", views_auth.ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/profile/", views_auth.ProfileView.as_view(), name="auth-profile"),
    path("auth/update-location/", views_auth.UpdateLocationView.as_view(), name="auth-update-location"),
    path("auth/detect-location/", views_auth.DetectLocationView.as_view(), name="auth-detect-location"),
]

ml_urlpatterns = [
    path("ml/recommendations/", views_ml.RecommendedDestinationsView.as_view(), name="ml-recommendations"),
    path("ml/safety/", views_ml.SafetyPredictionView.as_view(), name="ml-safety"),
    path("ml/budget/", views_ml.BudgetPredictionView.as_view(), name="ml-budget"),
    path("ml/best-route/", views_ml.BestRouteView.as_view(), name="ml-best-route"),
    path("ml/results/", views_ml.MLResultWebhookView.as_view(), name="ml-results-webhook"),
]

urlpatterns = [
    path("translate/", views.TranslateTextView.as_view(), name="translate-text"),
    path("places/osm-nearby/", views.OSMNearbyPlacesView.as_view(), name="osm-nearby-places"),
    *auth_urlpatterns,
    *ml_urlpatterns,

    # --- Compatibility routes matching the existing frontend's calls ---
    path("recommendations/personalized", views_compat.RecommendationsPersonalizedView.as_view(), name="compat-recommendations-personalized"),
    path("budget/summary", views_compat.BudgetSummaryView.as_view(), name="compat-budget-summary"),
    path("budget/summary/", views_compat.BudgetSummaryView.as_view(), name="compat-budget-summary-slash"),
    path("emergency/contacts", views_compat.EmergencyContactsCompatView.as_view(), name="compat-emergency-contacts"),
    path("nearby/hospitals", views_compat.NearbyHospitalsView.as_view(), name="compat-nearby-hospitals"),
    path("nearby/police", views_compat.NearbyPoliceView.as_view(), name="compat-nearby-police"),
    path("nearby/places", views_compat.NearbyPlacesCompatView.as_view(), name="compat-nearby-places"),
    path("navigation/route", views_compat.NavigationRouteView.as_view(), name="compat-navigation-route"),

    path("osm/essential-services/sync/", views_osm.OSMEssentialServiceSyncView.as_view(), name="osm-essential-sync"),
    path("osm/essential-services/nearby/", views_osm.OSMEssentialServiceNearbyView.as_view(), name="osm-essential-nearby"),
    path("osm/tourism-places/sync/", views_osm.OSMTourismPlaceSyncView.as_view(), name="osm-tourism-sync"),
    path("osm/tourism-places/nearby/", views_osm.OSMTourismPlaceNearbyView.as_view(), name="osm-tourism-nearby"),
    path("weather/current/", views_compat.WeatherByCoordinatesView.as_view(), name="compat-weather-current"),

    path("", include(router.urls)),
]
