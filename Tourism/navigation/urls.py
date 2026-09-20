from django.urls import path

from .views import (ActiveSessionsView, AlongRoutePlacesView, GPSReplayView,
                    ItineraryRouteView, NavigationDiagnosticsView,
                    NavigationEndView, NavigationHealthView,
                    NavigationModesView, NavigationProgressView, RoadRouteView,
                    RouteContextView, SelectAlternativeView)

urlpatterns = [
    path("road-route/", RoadRouteView.as_view(), name="navigation-road-route"),
    path("progress/", NavigationProgressView.as_view(), name="navigation-progress"),
    path("modes/", NavigationModesView.as_view(), name="navigation-modes"),
    path("diagnostics/", NavigationDiagnosticsView.as_view(), name="navigation-diagnostics"),
    path("itinerary-route/", ItineraryRouteView.as_view(), name="navigation-itinerary-route"),
    path("select-alternative/", SelectAlternativeView.as_view(), name="navigation-select-alternative"),
    path("along-route/", AlongRoutePlacesView.as_view(), name="navigation-along-route"),
    path("route-context/", RouteContextView.as_view(), name="navigation-route-context"),
    path("end/", NavigationEndView.as_view(), name="navigation-end"),
    path("sessions/active/", ActiveSessionsView.as_view(), name="navigation-active-session"),
    path("debug/replay/", GPSReplayView.as_view(), name="navigation-gps-replay"),
    path("health/", NavigationHealthView.as_view(), name="navigation-health"),
]
