from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import views
from . import views_auth
from . import views_admin
from . import views_compat
from . import views_family_safety
from . import views_images
from . import views_ml
from . import views_oauth
from . import views_osm
from .serializers import UserProfileSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserProfileSerializer(self.user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


router = DefaultRouter()
router.register("languages", views.LanguageViewSet, basename="language")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("destinations", views.DestinationViewSet, basename="destination")
router.register("destination-images", views.DestinationImageViewSet, basename="destination-image")
router.register("hotels", views.HotelViewSet, basename="hotel")
router.register("videos", views.DestinationVideoViewSet, basename="destination-video")
router.register("reviews", views.ReviewViewSet, basename="review")
router.register("ratings", views.RatingViewSet, basename="rating")
router.register("favorites", views.FavoriteViewSet, basename="favorite")
router.register("history", views.VisitHistoryViewSet, basename="visit-history")
router.register("budgets", views.BudgetViewSet, basename="budget")
router.register("alerts", views.AlertViewSet, basename="alert")
router.register("emergency-contacts", views.EmergencyContactViewSet, basename="emergency-contact")
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("device-tokens", views.DeviceTokenViewSet, basename="device-token")
router.register("osm-tourism", views.OSMTourismPlaceViewSet, basename="osm-tourism")
router.register("osm-essentials", views.OSMEssentialServiceViewSet, basename="osm-essentials")
router.register("safety/trusted-contacts", views_family_safety.TrustedContactViewSet, basename="trusted-contact")
router.register("safety/trips", views_family_safety.SharedTripViewSet, basename="shared-trip")
router.register("safety/sos", views_family_safety.SOSAlertViewSet, basename="sos-alert")
router.register("expense-feedback", views.TravelExpenseFeedbackViewSet, basename="expense-feedback")
router.register("risk-feedback", views.TravelRiskFeedbackViewSet, basename="risk-feedback")

urlpatterns = [
    # Auth endpoints
    path("auth/register/", views_auth.RegisterView.as_view(), name="auth-register"),
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/logout/", views_auth.LogoutView.as_view(), name="auth-logout"),
    path("auth/profile/", views_auth.ProfileView.as_view(), name="auth-profile"),
    path("auth/verify-email/", views_auth.VerifyEmailView.as_view(), name="auth-verify-email"),
    path("auth/verify-phone/", views_auth.VerifyPhoneView.as_view(), name="auth-verify-phone"),
    path("auth/resend-phone-otp/", views_auth.ResendPhoneOTPView.as_view(), name="auth-resend-phone-otp"),
    path("auth/resend-verification-email/", views_auth.ResendVerificationEmailView.as_view(), name="auth-resend-verification-email"),
    path("auth/forgot-password/", views_auth.ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password/", views_auth.ResetPasswordView.as_view(), name="auth-reset-password"),
    path("auth/change-password/", views_auth.ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/update-location/", views_auth.UpdateLocationView.as_view(), name="auth-update-location"),
    path("auth/detect-location/", views_auth.DetectLocationView.as_view(), name="auth-detect-location"),
    path("auth/google/callback/", views_oauth.GoogleOAuthCallbackView.as_view(), name="auth-google-callback"),
    path("auth/github/callback/", views_oauth.GithubOAuthCallbackView.as_view(), name="auth-github-callback"),

    # ML endpoints
    path("ml/recommendations/", views_ml.RecommendedDestinationsView.as_view(), name="ml-recommendations"),
    path("ml/safety/", views_ml.SafetyPredictionView.as_view(), name="ml-safety"),
    path("ml/budget/", views_ml.BudgetPredictionView.as_view(), name="ml-budget"),
    path("ml/best-route/", views_ml.BestRouteView.as_view(), name="ml-best-route"),
    path("ml/itinerary/", views_ml.ItineraryView.as_view(), name="ml-itinerary"),
    path("ml/results/", views_ml.MLResultWebhookView.as_view(), name="ml-results-webhook"),

    # Compatibility endpoints
    path("recommendations/personalized", views_compat.RecommendationsPersonalizedView.as_view(), name="compat-recommendations"),
    path("budget/summary/", views_compat.BudgetSummaryView.as_view(), name="compat-budget-summary"),
    path("emergency/contacts", views_compat.EmergencyContactsCompatView.as_view(), name="compat-emergency-contacts"),
    path("nearby/places", views_compat.NearbyPlacesCompatView.as_view(), name="compat-nearby-places"),
    path("nearby/hospitals", views_compat.NearbyHospitalsView.as_view(), name="compat-nearby-hospitals"),
    path("nearby/police", views_compat.NearbyPoliceView.as_view(), name="compat-nearby-police"),
    path("navigation/route", views_compat.NavigationRouteView.as_view(), name="compat-navigation-route"),
    path("weather/current/", views_compat.WeatherByCoordinatesView.as_view(), name="compat-weather-current"),
    path("places/osm-nearby/", views.OSMNearbyPlacesView.as_view(), name="places-osm-nearby"),

    # Research & Discovery endpoints
    path("destinations/research/", views.DestinationResearchView.as_view(), name="destination-research"),
    path("destinations/search-discover/", views.DestinationSearchDiscoverView.as_view(), name="destination-search-discover"),

    # Admin RBAC & Moderation endpoints
    path("admin/stats", views_admin.AdminStatsView.as_view(), name="admin-stats"),
    path("admin/users", views_admin.AdminUsersView.as_view(), name="admin-users"),
    path("admin/users/<int:id>/", views_admin.UpdateUserStatusView.as_view(), name="admin-user-detail"),
    path("admin/users/<int:id>/status", views_admin.UpdateUserStatusView.as_view(), name="admin-update-user-status"),
    path("admin/user-tracking/", views_admin.AdminUserTrackingView.as_view(), name="admin-user-tracking"),
    path("admin/pending-places/", views_admin.AdminPendingPlacesView.as_view(), name="admin-pending-places"),
    path("admin/pending-places/<int:id>/", views_admin.AdminPendingPlacesView.as_view(), name="admin-pending-places-action"),
    path("admin/pending-images/", views_admin.AdminPendingImagesView.as_view(), name="admin-pending-images"),
    path("admin/pending-images/<int:id>/", views_admin.AdminPendingImagesView.as_view(), name="admin-pending-images-action"),
    path("admin/emergencies/", views_admin.AdminEmergenciesView.as_view(), name="admin-emergencies"),
    path("admin/emergencies/<int:id>/resolve/", views_admin.AdminEmergenciesView.as_view(), name="admin-emergencies-resolve"),
    path("admin/destinations", views_admin.AdminDestinationsView.as_view(), name="admin-destinations"),
    path("admin/destinations/<int:id>", views_admin.AdminDestinationDetailView.as_view(), name="admin-destination-detail"),
    path("admin/alerts", views_admin.AdminAlertsView.as_view(), name="admin-alerts"),

    # Additional endpoints
    path("config/public/", views.PublicConfigView.as_view(), name="public-config"),
    path("translate/", views.TranslateTextView.as_view(), name="translate-text"),
    path("images/resolve/", views_images.ImageResolveView.as_view(), name="images-resolve"),
    path("hotels/search/", views.HotelSearchView.as_view(), name="hotel-search"),
    path("safety/trip-share/<uuid:token>/", views_family_safety.SharedTripPublicView.as_view(), name="shared-trip-public"),

    # Router includes
    path("", include(router.urls)),
]
