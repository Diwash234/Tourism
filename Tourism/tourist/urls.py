from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import views
from . import views_auth
from . import views_admin
from . import views_compat
from . import views_discovery
from . import views_family_safety
from . import views_images
from .services.ai_images import api as ai_images_api
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
router.register("safety/family-links", views_family_safety.FamilyLinkViewSet, basename="family-link")
router.register("expense-feedback", views.TravelExpenseFeedbackViewSet, basename="expense-feedback")
router.register("risk-feedback", views.TravelRiskFeedbackViewSet, basename="risk-feedback")
router.register("admin/destination-features", views.DestinationFeatureProfileViewSet, basename="admin-destination-features")
router.register("admin/risk-incidents", views.RiskIncidentAdminViewSet, basename="admin-risk-incidents")
router.register("admin/current-hazards", views.CurrentHazardAdminViewSet, basename="admin-current-hazards")
router.register("admin/risk-observations", views.RiskObservationAdminViewSet, basename="admin-risk-observations")
router.register("admin/destination-translations", views.DestinationTranslationAdminViewSet, basename="admin-destination-translations")
router.register("infrastructure-submissions", views.InfrastructureSubmissionViewSet, basename="infrastructure-submission")
router.register("news", views.RiskNewsReportViewSet, basename="risk-news")

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
    path("auth/capabilities/", views_auth.MyCapabilitiesView.as_view(), name="auth-capabilities"),
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
    path("budget/summary", views_compat.BudgetSummaryView.as_view(), name="compat-budget-summary-noslash"),
    path("budget/summary/", views_compat.BudgetSummaryView.as_view(), name="compat-budget-summary"),
    path("emergency/contacts", views_compat.EmergencyContactsCompatView.as_view(), name="compat-emergency-contacts"),
    path("nearby/places", views_compat.NearbyPlacesCompatView.as_view(), name="compat-nearby-places"),
    path("nearby/hospitals", views_compat.NearbyHospitalsView.as_view(), name="compat-nearby-hospitals"),
    path("nearby/police", views_compat.NearbyPoliceView.as_view(), name="compat-nearby-police"),
    path("navigation/route", views_compat.NavigationRouteView.as_view(), name="compat-navigation-route"),
    path("weather/current/", views_compat.WeatherByCoordinatesView.as_view(), name="compat-weather-current"),
    path("places/osm-nearby/", views.OSMNearbyPlacesView.as_view(), name="osm-nearby-places"),
    path("osm/essential-services/sync/", views_osm.OSMEssentialServiceSyncView.as_view(), name="osm-essential-sync"),
    path("osm/essential-services/nearby/", views_osm.OSMEssentialServiceNearbyView.as_view(), name="osm-essential-nearby"),
    path("osm/tourism-places/sync/", views_osm.OSMTourismPlaceSyncView.as_view(), name="osm-tourism-sync"),
    path("osm/tourism-places/nearby/", views_osm.OSMTourismPlaceNearbyView.as_view(), name="osm-tourism-nearby"),

    # Research & Discovery endpoints
    path("destinations/research/", views.DestinationResearchView.as_view(), name="destination-research"),
    path("destinations/search-discover/", views.DestinationSearchDiscoverView.as_view(), name="destination-search-discover"),
    path("admin/discovery/health-report/", views_discovery.DiscoveryHealthReportView.as_view(), name="admin-discovery-health-report"),
    path("admin/discovery/stats/", views_discovery.DiscoveryStatsView.as_view(), name="admin-discovery-stats"),
    path("admin/discovery/candidates/", views_discovery.DestinationCandidateListView.as_view(), name="admin-discovery-candidates"),
    path("admin/discovery/run-batch/", views_discovery.RunDiscoveryJobView.as_view(), name="admin-discovery-run-batch"),
    path("admin/discovery/bulk-action/", views_discovery.DiscoveryBulkActionView.as_view(), name="admin-discovery-bulk-action"),
    path("admin/discovery/candidates/<int:pk>/action/", views_discovery.CandidateActionView.as_view(), name="admin-discovery-candidate-action"),

    # Admin RBAC & Moderation endpoints
    path("admin/stats", views_admin.AdminStatsView.as_view(), name="admin-stats"),
    path("admin/users", views_admin.AdminUsersView.as_view(), name="admin-users"),
    path("admin/users/<int:id>/", views_admin.AdminUsersDetailView.as_view(), name="admin-user-detail-full"),
    path("admin/users/<int:id>/status", views_admin.UpdateUserStatusView.as_view(), name="admin-update-user-status"),
    path("admin/users/<int:id>/actions", views_admin.AdminUserAccessActionView.as_view(), name="admin-user-access-action"),
    path("admin/users/<int:id>/send-verification", views_admin.AdminSendVerificationView.as_view(), name="admin-send-verification"),
    path("admin/data-explorer/", views_admin.AdminDataExplorerView.as_view(), name="admin-data-explorer"),
    path("admin/cms/", views_admin.AdminCMSView.as_view(), name="admin-cms"),
    path("admin/staff-capabilities/", views_admin.StaffCapabilityManagementView.as_view(), name="admin-staff-capabilities"),
    path("admin/infrastructure-submissions/", views_admin.InfrastructureModerationView.as_view(), name="admin-infrastructure-submissions"),
    path("admin/infrastructure-submissions/<int:id>/", views_admin.InfrastructureModerationView.as_view(), name="admin-infrastructure-submission-action"),
    path("admin/ml-data-pipeline/", views_admin.MLDataPipelineView.as_view(), name="admin-ml-data-pipeline"),
    path("admin/ml/status/", views_admin.MLDataPipelineView.as_view(), name="admin-ml-status"),
    path("admin/review-moderation/", views_admin.AdminReviewModerationView.as_view(), name="admin-review-moderation"),
    path("admin/notifications/", views_admin.AdminNotificationManagementView.as_view(), name="admin-notifications"),
    path("admin/search/", views_admin.AdminGlobalSearchView.as_view(), name="admin-global-search"),
    path("admin/media-library/", views_admin.AdminMediaLibraryView.as_view(), name="admin-media-library"),
    path("admin/datasets/", views_admin.AdminDatasetManagerView.as_view(), name="admin-datasets"),
    path("admin/reports/", views_admin.AdminReportsView.as_view(), name="admin-reports"),
    path("admin/feedback", views_admin.FeedbackListView.as_view(), name="admin-feedback"),
    path("admin/feedback/<int:id>/reply", views_admin.FeedbackReplyView.as_view(), name="admin-feedback-reply"),
    path("feedback", views_admin.PublicFeedbackCreateView.as_view(), name="public-feedback"),
    path("admin/fetch-images/", views_admin.FetchWebImagesView.as_view(), name="admin-fetch-images"),
    path("admin/generate-ai-images/", views_admin.GenerateAIImagesView.as_view(), name="admin-generate-ai-images"),
    path("admin/download-ai-images/", views_admin.DownloadAIImagesView.as_view(), name="admin-download-ai-images"),
    path("admin/images/<int:id>", views_admin.DeleteImageView.as_view(), name="admin-delete-image"),
    path("admin/user-tracking/", views_admin.AdminUserTrackingView.as_view(), name="admin-user-tracking"),
    path("admin/pending-places/", views_admin.AdminPendingPlacesView.as_view(), name="admin-pending-places"),
    path("admin/pending-places/<int:id>/", views_admin.AdminPendingPlacesView.as_view(), name="admin-pending-places-action"),
    path("admin/pending-images/", views_admin.AdminPendingImagesView.as_view(), name="admin-pending-images"),
    path("admin/pending-images/<int:id>/", views_admin.AdminPendingImagesView.as_view(), name="admin-pending-images-action"),
    path("admin/emergencies/", views_admin.AdminEmergenciesView.as_view(), name="admin-emergencies"),
    path("admin/emergencies/<int:id>/resolve/", views_admin.AdminEmergenciesView.as_view(), name="admin-emergencies-resolve"),
    path("admin/destinations", views_admin.AdminDestinationsView.as_view(), name="admin-destinations"),
    path("admin/destinations/<int:id>", views_admin.AdminDestinationDetailView.as_view(), name="admin-destination-detail"),
    path("admin/destinations/<int:id>/images", views_admin.AdminDestinationImageView.as_view(), name="admin-destination-images"),
    path("admin/alerts", views_admin.AdminAlertsView.as_view(), name="admin-alerts"),

    # Additional endpoints
    path("config/public/", views.PublicConfigView.as_view(), name="public-config"),
    path("translate/", views.TranslateTextView.as_view(), name="translate-text"),
    path("images/resolve/", views_images.ImageResolveView.as_view(), name="images-resolve"),
    # Multi-source Image Acquisition & Provenance Pipeline API
    path("destinations/<str:slug>/images", views_images.DestinationImagesListView.as_view(), name="destination-images-list-no-slash"),
    path("destinations/<str:slug>/images/", views_images.DestinationImagesListView.as_view(), name="destination-images-list"),
    path("destinations/<str:slug>/images/discover", views_images.DestinationImagesDiscoverView.as_view(), name="destination-images-discover-no-slash"),
    path("destinations/<str:slug>/images/discover/", views_images.DestinationImagesDiscoverView.as_view(), name="destination-images-discover"),
    path("destinations/<str:slug>/images/refresh", views_images.DestinationImagesRefreshView.as_view(), name="destination-images-refresh-no-slash"),
    path("destinations/<str:slug>/images/refresh/", views_images.DestinationImagesRefreshView.as_view(), name="destination-images-refresh"),
    path("destinations/<str:slug>/images/<int:image_id>/set-cover", views_images.DestinationImageSetCoverView.as_view(), name="destination-images-set-cover-no-slash"),
    path("destinations/<str:slug>/images/<int:image_id>/set-cover/", views_images.DestinationImageSetCoverView.as_view(), name="destination-images-set-cover"),

    # AI Nepal image dataset platform
    path("ai-images/destinations", ai_images_api.DestinationListView.as_view(), name="ai-image-destinations"),
    path("ai-images/destinations/<int:pk>", ai_images_api.DestinationDetailView.as_view(), name="ai-image-destination-detail"),
    path("ai-images/destinations/<int:pk>/images", ai_images_api.DestinationImagesView.as_view(), name="ai-image-destination-images"),
    path("ai-images/generate", ai_images_api.GenerateImagesView.as_view(), name="ai-image-generate"),
    path("ai-images/search", ai_images_api.SemanticSearchView.as_view(), name="ai-image-search"),
    path("ai-images/jobs", ai_images_api.JobsListView.as_view(), name="ai-image-jobs"),
    path("ai-images/images/<int:pk>/validate", ai_images_api.ImageValidateView.as_view(), name="ai-image-validate"),
    path("ai-images/images/<int:pk>/match", ai_images_api.ImageMatchView.as_view(), name="ai-image-match"),
    path("ai-images/images/<int:pk>/moderate", ai_images_api.ImageModerateView.as_view(), name="ai-image-moderate"),
    path("hotels/search/", views.HotelSearchView.as_view(), name="hotel-search"),
    path("destinations/autocomplete/", views.DestinationAutocompleteView.as_view(), name="destination-autocomplete"),
    path("destinations/mood-recommendations/", views.MoodRecommendationsView.as_view(), name="mood-recommendations"),
    path("gallery/featured/", views.FeaturedGalleryView.as_view(), name="featured-gallery"),
    path("gallery/districts/", views.DistrictGalleryView.as_view(), name="district-gallery"),
    path("destinations/<str:destination_ref>/risk/", views.DestinationRiskAssessmentView.as_view(), name="destination-risk-assessment"),
    path("recommendation-events/", views.RecommendationEventView.as_view(), name="recommendation-events"),
    path("destinations/<str:destination_ref>/emergency/", views.DestinationEmergencyServicesView.as_view(), name="destination-emergency-services"),
    path("emergency/nearby/", views.NearbyEmergencyServicesView.as_view(), name="nearby-emergency-services"),
    path("routing/metrics/", views.RouteMetricsView.as_view(), name="route-metrics"),
    # Deterministic Nepal-themed SVG postcards (no more repeated stock photos)
    path("postcard/<path:path_info>", views.destination_postcard, name="destination-postcard"),
    path("safety/trip-share/<uuid:token>/", views_family_safety.SharedTripPublicView.as_view(), name="shared-trip-public"),
    path("safety/family/members/", views_family_safety.FamilyMembersView.as_view(), name="family-members"),

    # Router includes
    path("", include(router.urls)),
]
