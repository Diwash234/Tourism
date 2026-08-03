# from django.urls import path, include
# from rest_framework.routers import DefaultRouter

# from . import views

# router = DefaultRouter()
# router.register("trusted-contacts", views.TrustedContactViewSet, basename="trusted-contact")
# router.register("trips", views.SharedTripViewSet, basename="shared-trip")
# router.register("sos", views.SOSAlertViewSet, basename="sos-alert")

# urlpatterns = [
#     path("shared/<uuid:token>/", views.SharedTripPublicView.as_view(), name="shared-trip-public"),
#     path("", include(router.urls)),
# ]