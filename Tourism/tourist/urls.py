from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views, views_auth, views_ml


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


auth_urlpatterns = [
    path("auth/register/", views_auth.RegisterView.as_view()),
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("auth/token/verify/", TokenVerifyView.as_view()),
    path("auth/logout/", views_auth.LogoutView.as_view()),
    path("auth/verify-email/", views_auth.VerifyEmailView.as_view()),
    path("auth/resend-verification/", views_auth.ResendVerificationEmailView.as_view()),
    path("auth/forgot-password/", views_auth.ForgotPasswordView.as_view()),
    path("auth/reset-password/", views_auth.ResetPasswordView.as_view()),
    path("auth/change-password/", views_auth.ChangePasswordView.as_view()),
    path("auth/profile/", views_auth.ProfileView.as_view()),
    path("auth/update-location/", views_auth.UpdateLocationView.as_view()),
    path("auth/detect-location/", views_auth.DetectLocationView.as_view()),
]


ml_urlpatterns = [
    path(
        "ml/recommendations/",
        views_ml.RecommendedDestinationsView.as_view(),
        name="ml-recommendations",
    ),
    path(
        "ml/safety/",
        views_ml.SafetyPredictionView.as_view(),
        name="ml-safety",
    ),
    path(
        "ml/budget/",
        views_ml.BudgetPredictionView.as_view(),
        name="ml-budget",
    ),
    path(
        "ml/results/",
        views_ml.MLResultWebhookView.as_view(),
        name="ml-results-webhook",
    ),
]


# Frontend compatibility routes
frontend_aliases = [

    # Translation
    path(
        "translation/translate",
        views.TranslateTextView.as_view(),
        name="frontend-translate",
    ),

    # User profile
    path(
        "users/profile",
        views_auth.ProfileView.as_view(),
        name="frontend-profile",
    ),

    # User data
    path(
        "users/favorites",
        views.FavoriteViewSet.as_view({"get": "list"}),
        name="frontend-favorites",
    ),

    path(
        "users/history",
        views.VisitHistoryViewSet.as_view({"get": "list"}),
        name="frontend-history",
    ),

    path(
        "users/notifications",
        views.NotificationViewSet.as_view({"get": "list"}),
        name="frontend-notifications",
    ),

    # ML aliases
    path(
        "recommendations/personalized",
        views_ml.RecommendedDestinationsView.as_view(),
        name="frontend-recommendations",
    ),

    path(
        "budget/summary",
        views_ml.BudgetPredictionView.as_view(),
        name="frontend-budget-summary",
    ),
]


urlpatterns = [
    path("translate/", views.TranslateTextView.as_view(), name="translate-text"),

    *auth_urlpatterns,

    *ml_urlpatterns,

    *frontend_aliases,

    path("", include(router.urls)),
]