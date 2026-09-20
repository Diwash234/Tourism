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
from django.db.models import Count
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import navigation_service, route_engine
from .serializers import (ItineraryRouteRequestSerializer,
                          ProgressRequestSerializer, RouteRequestSerializer,
                          SelectAlternativeSerializer)


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
        route_id = navigation_service.create_session(
            route, endpoints={"start": start, "destination": dest, "mode": mode})
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


class NavigationDiagnosticsView(APIView):
    """Admin-only: are users getting real road routes or silent fallbacks?"""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from .models import RouteDiagnostics
        window_hours = int(request.query_params.get("hours", 24))
        from django.utils import timezone
        import datetime as _dt
        since = timezone.now() - _dt.timedelta(hours=window_hours)
        qs = RouteDiagnostics.objects.filter(created_at__gte=since)
        by_provider = {row["provider"]: row["n"] for row in
                       qs.values("provider").annotate(n=Count("id"))}
        total = sum(by_provider.values())
        fallbacks = sum(n for p, n in by_provider.items() if p != "osrm")
        avg_ms = 0
        rows = list(qs[:100])
        if rows:
            avg_ms = round(sum(r.route_time_ms for r in rows) / len(rows), 1)
        return Response({
            "window_hours": window_hours,
            "total_requests": total,
            "by_provider": by_provider,
            "fallback_count": fallbacks,
            "fallback_rate": round(fallbacks / total, 4) if total else None,
            "avg_route_time_ms": avg_ms,
            "recent": [{
                "provider": r.provider, "mode": r.mode, "distance_m": r.distance_m,
                "duration_s": r.duration_s, "fallback": r.fallback,
                "route_time_ms": r.route_time_ms, "alternatives": r.alternatives,
                "created_at": r.created_at,
            } for r in rows[:50]],
        })


class ItineraryRouteView(APIView):
    """POST /api/v1/navigation/itinerary-route/ — multi-stop road routing.

    Each leg is routed independently through the same provider chain; the
    response carries per-leg geometry/steps/route_id plus honest totals.
    Tourism intelligence (which stops, in which order) stays OUT of the
    routing providers — the itinerary engine supplies coordinates only.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ItineraryRouteRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        mode = d["mode"]
        points = [(d["start"]["latitude"], d["start"]["longitude"])] + [
            (s["latitude"], s["longitude"]) for s in d["stops"]]
        names = ["Start"] + [(s.get("name") or f"Stop {i + 1}")
                             for i, s in enumerate(d["stops"])]

        legs = []
        total_m = total_s = 0.0
        sources = set()
        for i in range(len(points) - 1):
            try:
                result, _cached = route_engine.cached_route(
                    points[i], points[i + 1], mode, request=request)
            except route_engine.RateLimited:
                return Response({"status": "error", "error": "rate_limited"},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)
            route = dict(result["route"])
            route_id = navigation_service.create_session(
                route, endpoints={"start": points[i], "destination": points[i + 1],
                                  "mode": mode})
            sources.add(route["source"])
            total_m += route["distance_m"]
            total_s += route["duration_s"]
            legs.append({
                "leg": i,
                "from": {"name": names[i], "latitude": points[i][0], "longitude": points[i][1]},
                "to": {"name": names[i + 1], "latitude": points[i + 1][0],
                       "longitude": points[i + 1][1],
                       "stop_id": d["stops"][i].get("id")},
                "route_id": route_id,
                "distance_m": route["distance_m"],
                "duration_s": route["duration_s"],
                "geometry": route["geometry"],
                "steps": route.get("steps", []),
                "source": route["source"],
                "note": route.get("note"),
            })

        # one diagnostics summary row for itinerary usage
        try:
            from .models import RouteDiagnostics
            import time as _t
            primary = "osrm" if sources == {"osrm"} else "fallback_mixed" if len(sources) > 1 else next(iter(sources))
            RouteDiagnostics.objects.create(
                provider=f"itinerary:{primary}", mode=mode,
                distance_m=round(total_m, 1), duration_s=round(total_s, 1),
                fallback=primary != "osrm", route_time_ms=0,
                alternatives=len(legs) - 1,
                start_lat=points[0][0], start_lng=points[0][1],
                dest_lat=points[-1][0], dest_lng=points[-1][1])
        except Exception:
            pass

        return Response({
            "status": "success",
            "mode": mode,
            "legs": legs,
            "totals": {
                "legs": len(legs),
                "distance_m": round(total_m, 1),
                "duration_s": round(total_s, 1),
                "sources": sorted(sources),
            },
        })


class SelectAlternativeView(APIView):
    """Swap the active session to one of the alternatives returned earlier."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = SelectAlternativeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        route = navigation_service.get_session(d["route_id"])
        if route is None:
            return Response({"status": "error", "error": "unknown_route"},
                            status=status.HTTP_404_NOT_FOUND)
        ep = route.get("_endpoints") or {}
        start, dest, mode = ep.get("start"), ep.get("destination"), ep.get("mode", "driving")
        if not start or not dest:
            return Response({"status": "error", "error": "session_missing_endpoints"},
                            status=status.HTTP_409_CONFLICT)
        result, _cached = route_engine.cached_route(
            tuple(start), tuple(dest), mode, request=request, want_alternatives=True)
        alts = result.get("alternatives") or []
        if d["index"] >= len(alts):
            return Response({"status": "error", "error": "no_such_alternative",
                             "available": len(alts)},
                            status=status.HTTP_404_NOT_FOUND)
        chosen = dict(alts[d["index"]])
        # steps: reuse primary-route step granularity only when geometry matches;
        # otherwise give honest endpoint-level guidance.
        if not chosen.get("steps"):
            chosen["steps"] = [
                {"instruction": "Head out (alternative route)", "maneuver": "depart",
                 "distance_m": chosen["distance_m"], "duration_s": chosen["duration_s"]},
                {"instruction": "Arrive at destination", "maneuver": "arrive",
                 "distance_m": 0, "duration_s": 0},
            ]
        new_id = navigation_service.create_session(chosen, endpoints=ep)
        return Response({"status": "success", "route": {
            "route_id": new_id, **{k: chosen.get(k) for k in
            ("distance_m", "duration_s", "geometry", "bounds", "mode", "source", "note")}},
            "steps": chosen.get("steps", [])})


class AlongRoutePlacesView(APIView):
    """GET /api/v1/navigation/along-route/?route_id=&category=&radius_m=

    Places sorted by distance ALONG the route (projection onto the route
    polyline), not straight-line-from-user — the navigation-aware nearby
    view. Straight-line values are included for honesty.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        route_id = request.query_params.get("route_id", "")
        category = request.query_params.get("category", "hospital")
        try:
            radius_m = float(request.query_params.get("radius_m", 3000))
        except ValueError:
            radius_m = 3000.0
        route = navigation_service.get_session(route_id)
        if route is None:
            return Response({"status": "error", "error": "unknown_route"},
                            status=status.HTTP_404_NOT_FOUND)
        geometry = route.get("geometry") or []
        if len(geometry) < 2:
            return Response({"status": "error", "error": "route_has_no_geometry"},
                            status=status.HTTP_409_CONFLICT)

        from tourist.models import Destination, Hospital, PoliceStation
        from .map_matching import haversine_m, match_point_to_route
        from .fallback_providers import bearing_deg  # noqa: F401 (kept light)

        candidates = []  # (name, type, lat, lng)
        if category == "hospital":
            candidates = [(h.name, "hospital", float(h.latitude), float(h.longitude))
                          for h in Hospital.objects.exclude(latitude=None)[:400]]
        elif category == "police":
            candidates = [(p.name, "police", float(p.latitude), float(p.longitude))
                          for p in PoliceStation.objects.exclude(latitude=None)[:400]]
        elif category == "attraction":
            candidates = [(dd.name, "attraction", float(dd.latitude), float(dd.longitude))
                          for dd in Destination.publicly_visible()
                          .exclude(latitude=None)[:800]]
        elif category == "hotel":
            from tourist.models import Hotel
            candidates = [(h.name, "hotel", float(h.latitude), float(h.longitude))
                          for h in Hotel.objects.exclude(latitude=None)[:400]]
        else:
            return Response({"status": "error", "error": "unsupported_category",
                             "supported": ["hospital", "police", "attraction", "hotel"]},
                            status=status.HTTP_400_BAD_REQUEST)

        # corridor prefilter (cheap), then exact polyline projection
        lats = [g[0] for g in geometry]
        lngs = [g[1] for g in geometry]
        pad = max(0.05, radius_m / 111320.0)
        items = []
        for name, ctype, lat, lng in candidates:
            if not (min(lats) - pad <= lat <= max(lats) + pad
                    and min(lngs) - pad <= lng <= max(lngs) + pad):
                continue
            m = match_point_to_route((lat, lng), geometry)
            if m["distance_from_route_m"] > radius_m:
                continue
            items.append({
                "name": name, "type": ctype,
                "latitude": lat, "longitude": lng,
                "along_route_m": m["traveled_m"],
                "detour_m": m["distance_from_route_m"],
                "snapped": m["snapped"],
            })
        items.sort(key=lambda x: x["along_route_m"])
        return Response({"status": "success", "category": category,
                         "radius_m": radius_m, "count": len(items),
                         "items": items[:50]})


class RouteContextView(APIView):
    """GET /api/v1/navigation/route-context/?route_id=

    Context layers ONLY (safety, weather) — they annotate the route and
    never alter it; routing truth stays with the provider.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        route = navigation_service.get_session(request.query_params.get("route_id", ""))
        if route is None:
            return Response({"status": "error", "error": "unknown_route"},
                            status=status.HTTP_404_NOT_FOUND)
        geometry = route.get("geometry") or []
        if not geometry:
            return Response({"status": "error", "error": "route_has_no_geometry"},
                            status=status.HTTP_409_CONFLICT)

        # --- safety: active hazards near the corridor (~5 km) -------------
        from tourist.models import CurrentHazard, Destination
        from .map_matching import haversine_m
        lats = [g[0] for g in geometry]
        lngs = [g[1] for g in geometry]
        pad = 0.06
        hazards = []
        qs = (CurrentHazard.objects
              .filter(destination__latitude__gte=min(lats) - pad,
                      destination__latitude__lte=max(lats) + pad,
                      destination__longitude__gte=min(lngs) - pad,
                      destination__longitude__lte=max(lngs) + pad)
              .select_related("destination")[:20])
        for hz in qs:
            dlat, dlng = float(hz.destination.latitude), float(hz.destination.longitude)
            # distance from the corridor centreline (sampled)
            near = min(haversine_m(dlat, dlng, g[0], g[1]) for g in geometry[::max(1, len(geometry) // 20)])
            if near > 5000:
                continue
            hazards.append({
                "title": hz.title, "hazard_type": hz.hazard_type,
                "severity": hz.severity, "place": hz.destination.name,
                "distance_from_route_m": round(near, 0),
            })

        # --- weather: best-effort at route midpoint (labelled) -------------
        from tourist.utils import get_current_weather
        mid = geometry[len(geometry) // 2]
        weather = get_current_weather(mid[0], mid[1])
        return Response({
            "status": "success",
            "safety": {"warnings": hazards,
                       "note": "Context layer only — warnings never alter the route."},
            "weather": {"data": weather,
                        "note": ("Live conditions at route midpoint" if weather
                                 else "Weather unavailable (no API key / unreachable) — context layer only.")},
        })
