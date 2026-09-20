"""Navigation subsystem endpoints.

POST /api/v1/navigation/road-route/  — road route preview (canonical body)
POST /api/v1/navigation/progress/    — live navigation progress
GET  /api/v1/navigation/modes/       — modes the configured provider serves

The legacy POST /api/v1/navigation/route (tourism-graph alias in
views_compat) is intentionally untouched — the tourism graph stays the AI
recommendation/itinerary router, per the target architecture.
"""
from __future__ import annotations

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import navigation_service, route_engine
from .serializers import ProgressRequestSerializer, RouteRequestSerializer


class RoadRouteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RouteRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        start = (d["start"]["latitude"], d["start"]["longitude"])
        dest = (d["destination"]["latitude"], d["destination"]["longitude"])
        mode = d["mode"]
        try:
            result, cached = route_engine.cached_route(
                start, dest, mode, request=request,
                want_alternatives=d["alternatives"])
        except route_engine.RateLimited:
            return Response(
                {"status": "error", "error": "rate_limited",
                 "detail": f"Max {getattr(settings, 'ROUTING_RATE_LIMIT', 30)} "
                           "route requests/minute."},
                status=status.HTTP_429_TOO_MANY_REQUESTS)

        route = dict(result["route"])
        route_id = navigation_service.create_session(route)
        return Response({
            "status": "success",
            "route": {
                "route_id": route_id,
                "distance_m": route["distance_m"],
                "duration_s": route["duration_s"],
                "geometry": route["geometry"],
                "bounds": route.get("bounds"),
                "mode": route["mode"],
                "source": route["source"],
                "note": route.get("note"),
            },
            "alternatives": [
                {k: a.get(k) for k in ("distance_m", "duration_s", "geometry", "bounds", "source")}
                for a in result.get("alternatives", [])
            ],
            "steps": route.get("steps", []),
            "cached": cached,
        })


class NavigationProgressView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ProgressRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        route = navigation_service.get_session(d["route_id"])
        if route is None:
            return Response(
                {"status": "error", "error": "unknown_route",
                 "detail": "Route session expired or never existed — request a new route."},
                status=status.HTTP_404_NOT_FOUND)
        progress = navigation_service.compute_progress(
            route, d["latitude"], d["longitude"],
            heading=d.get("heading"), accuracy=d.get("accuracy"))
        return Response({"status": "success", "route_id": d["route_id"], **progress})


class NavigationModesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        provider = route_engine.get_provider()
        return Response({
            "provider": provider.name,
            "configured": bool(getattr(settings, "ROUTING_BASE_URL", "")),
            "modes": list(provider.supported_modes),
            "fallbacks": ["bundled_graph_estimate", "straight_line_estimate"],
        })
