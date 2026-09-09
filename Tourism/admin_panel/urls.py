from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("hotel-assignments", views.HotelAssignmentViewSet, basename="hotel-assignment")
router.register("tasks", views.AdminTaskViewSet, basename="admin-task")

urlpatterns = [
    path("my-hotels/", views.MyHotelsView.as_view(), name="admin-panel-my-hotels"),
    path("tasks/<int:pk>/action/", views.AdminTaskActionView.as_view(), name="admin-panel-task-action"),
    path("my-performance/", views.MyPerformanceView.as_view(), name="admin-panel-my-performance"),
    path("support/tickets/", views.SupportTicketListView.as_view(), name="admin-panel-support-tickets"),
    path("support/tickets/<int:pk>/action/", views.SupportTicketActionView.as_view(), name="admin-panel-support-action"),
    path("my-bookings/", views.MyBookingsView.as_view(), name="admin-panel-my-bookings"),
    path("my-bookings/<int:pk>/action/", views.BookingActionView.as_view(), name="admin-panel-booking-action"),
    path("dashboard-summary/", views.AdminDashboardSummaryView.as_view(), name="admin-panel-dashboard-summary"),
    path("analytics/",views.AdminAnalyticsView.as_view(), name="admin-panel-analytics",
),
    path("destinations-missing-images/", views.DestinationsMissingImagesView.as_view(), name="admin-panel-destinations-missing-images"),
    path("", include(router.urls)),
]