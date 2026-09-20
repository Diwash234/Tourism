from django.urls import path

from .views import (AlongRoutePlacesView, ItineraryRouteView,
                    NavigationDiagnosticsView, NavigationModesView,
                    NavigationProgressView, RoadRouteView, RouteContextView,
                    SelectAlternativeView)

urlpatterns = [
    path("road-route/", RoadRouteView.as_view(), name="navigation-road-route"),
    path("progress/", NavigationProgressView.as_view(), name="navigation-progress"),
    path("modes/", NavigationModesView.as_view(), name="navigation-modes"),
    path("diagnostics/", NavigationDiagnosticsView.as_view(), name="navigation-diagnostics"),
    path("itinerary-route/", ItineraryRouteView.as_view(), name="navigation-itinerary-route"),
    path("select-alternative/", SelectAlternativeView.as_view(), name="navigation-select-alternative"),
    path("along-route/", AlongRoutePlacesView.as_view(), name="navigation-along-route"),
    path("route-context/", RouteContextView.as_view(), name="navigation-route-context"),
]
