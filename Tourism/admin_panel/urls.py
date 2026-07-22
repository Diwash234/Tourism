from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("hotel-assignments", views.HotelAssignmentViewSet, basename="hotel-assignment")
router.register("tasks", views.AdminTaskViewSet, basename="admin-task")

urlpatterns = [
    path("my-hotels/", views.MyHotelsView.as_view(), name="admin-panel-my-hotels"),
    path("dashboard-summary/", views.AdminDashboardSummaryView.as_view(), name="admin-panel-dashboard-summary"),
    path("", include(router.urls)),
]