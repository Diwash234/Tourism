from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("device-tokens", views.DeviceTokenViewSet, basename="device-token")

urlpatterns = router.urls