from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"logs", views.AuditLogViewSet, basename="audit-logs")
router.register(r"errors", views.ErrorEventViewSet, basename="audit-errors")
router.register(r"health", views.HealthSampleViewSet, basename="audit-health")

urlpatterns = [
    path("", include(router.urls)),
    path("report-error/", views.report_frontend_error, name="audit-report-error"),
]
