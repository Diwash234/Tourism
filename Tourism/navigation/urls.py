from django.urls import path

from .views import NavigationModesView, NavigationProgressView, RoadRouteView

urlpatterns = [
    path("road-route/", RoadRouteView.as_view(), name="navigation-road-route"),
    path("progress/", NavigationProgressView.as_view(), name="navigation-progress"),
    path("modes/", NavigationModesView.as_view(), name="navigation-modes"),
]
