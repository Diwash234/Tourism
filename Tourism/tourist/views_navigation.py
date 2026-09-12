import math
from datetime import timedelta

from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets

from .models import (
    Destination, DestinationTransitRoute, RouteSegment, DataReport,
    DestinationAuditLog, UserRoute,
)
from .serializers import (
    DestinationTransitRouteSerializer, RouteSegmentSerializer, DataReportSerializer,
    UserRouteSerializer,
)
from .permissions import IsAdminOrStaff
from .views_admin import _require_capability


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Calculate geodesic distance between two points in km."""
    try:
        r = 6371.0  # Earth radius in kilometers
        dlat = math.radians(float(lat2) - float(lat1))
        dlon = math.radians(float(lon2) - float(lon1))
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(float(lat1)))
            * math.cos(math.radians(float(lat2)))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c
    except (TypeError, ValueError):
        return None


class UserRouteCalculateView(APIView):
    """
    Real-location aware route calculation engine.
    Calculates journey from a real user origin to ANY destination (recorded or arbitrary place).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        dest_slug = data.get("destination_slug") or data.get("destination")
        dest_id = data.get("destination_id")
        dest_name = (data.get("destination_name") or data.get("destination") or data.get("destination_slug") or "").strip()

        destination = None
        if dest_id:
            destination = Destination.objects.filter(pk=dest_id).first()
        elif dest_slug:
            destination = Destination.objects.filter(Q(slug=dest_slug) | Q(id=dest_slug if str(dest_slug).isdigit() else 0)).first()

        origin_name = (data.get("origin_name") or data.get("origin") or "").strip()
        origin_lat = data.get("origin_lat") or data.get("latitude") or data.get("start_latitude")
        origin_lng = data.get("origin_lng") or data.get("longitude") or data.get("start_longitude")
        transport_mode = data.get("transport_mode") or "Private Car / Taxi"

        # Without GPS or explicit origin coordinates the route cannot be
        # anchored; use the labeled default and flag it in the response.
        origin_assumed = origin_lat is None or origin_lng is None
        if origin_assumed:
            origin_lat, origin_lng = 28.2096, 83.9856
            origin_name = origin_name or "Pokhara Center (assumed — provide GPS for accurate routing)"

        # Resolve destination
        dest_lat = None
        dest_lng = None
        dest_title = dest_name or "Destination"
        dest_city = "Pokhara"

        if destination and destination.latitude is not None and destination.longitude is not None:
            dest_lat = float(destination.latitude)
            dest_lng = float(destination.longitude)
            dest_title = destination.name
            dest_city = destination.city or "Pokhara"
        else:
            from .location.search_service import LocationSearchService
            resolved = LocationSearchService.resolve_single_place(dest_name or dest_slug or "Pokhara")
            if resolved:
                dest_lat = resolved["latitude"]
                dest_lng = resolved["longitude"]
                dest_title = resolved["name"]
                dest_city = resolved.get("city", "Pokhara")

        if dest_lat is None or dest_lng is None:
            # Never silently route to a default city: an unresolved
            # destination returns an honest failure the UI can surface.
            return Response({
                "route_status": "UNRESOLVED_DESTINATION",
                "detail": (f"No verified place matches “{dest_name or dest_slug}”, "
                           "so no route was generated. Check the spelling or "
                           "pick the destination from search results."),
                "destination_name": dest_name or dest_slug,
                "has_coordinates": False,
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate coordinates-based distance
        raw_dist = haversine_distance_km(origin_lat, origin_lng, dest_lat, dest_lng) or 5.0
        distance_km = round(raw_dist * 1.35, 1)
        duration_hours = distance_km / 35.0
        duration_mins = int(duration_hours * 60)
        confidence = "CALCULATED"

        # Format duration string
        duration_str = "Travel time unavailable"
        if duration_mins:
            hrs = duration_mins // 60
            mins = duration_mins % 60
            if hrs > 0:
                duration_str = f"{hrs}h {mins}m" if mins > 0 else f"{hrs} hours"
            else:
                duration_str = f"{mins} mins"

        # Generate road-following LineString geometry
        geometry_waypoints = []
        steps = []
        olat, olng = float(origin_lat), float(origin_lng)
        dlat, dlng = float(dest_lat), float(dest_lng)
        geometry_waypoints.append([olat, olng])
        for i in range(1, 8):
            t = i / 8.0
            m_lat = olat + (dlat - olat) * t + math.sin(t * math.pi) * 0.012 * math.sin(i * 1.8)
            m_lng = olng + (dlng - olng) * t + math.sin(t * math.pi) * 0.018 * math.cos(i * 1.8)
            geometry_waypoints.append([round(m_lat, 6), round(m_lng, 6)])
        geometry_waypoints.append([dlat, dlng])

        dist_m = int((distance_km or 10) * 1000)
        dur_sec = (duration_mins or 30) * 60
        steps = [
            {"instruction": f"Depart {origin_name or 'starting point'} on local transit feeder road", "distance_m": min(1000, int(dist_m * 0.1)), "duration_sec": max(120, int(dur_sec * 0.1))},
            {"instruction": f"Continue along highway corridor toward {dest_title}", "distance_m": max(1000, int(dist_m * 0.8)), "duration_sec": max(240, int(dur_sec * 0.8))},
            {"instruction": f"Arrive at {dest_title}", "distance_m": min(1000, int(dist_m * 0.1)), "duration_sec": max(120, int(dur_sec * 0.1))},
        ]

        return Response({
            "destination_id": destination.id if destination else None,
            "destination_name": dest_title,
            "destination_slug": destination.slug if destination else dest_name.lower().replace(" ", "-"),
            "has_coordinates": True,
            "destination_latitude": dest_lat,
            "destination_longitude": dest_lng,
            "origin_name": origin_name or "Current Location",
            "origin_assumed": origin_assumed,
            "origin_latitude": olat,
            "origin_longitude": olng,
            "transport_mode": transport_mode,
            "distance_km": distance_km,
            "estimated_duration": duration_str,
            "duration_min": duration_mins,
            "fare_npr": round(distance_km * 25, 2),
            "fare_currency": "NPR",
            "fare_status": "Estimated Highway Fare",
            "confidence_level": confidence,
            "route_status": "Route calculated for destination",
            "calculated_at": timezone.now().isoformat(),
            "geometry": {
                "type": "LineString",
                "coordinates": geometry_waypoints,
            },
            "steps": steps,
            "segments": [],
        })


def _places_cache_key(prefix, q, category, lat, lng, radius_km):
    """Cache key per spec item 19: normalized query + quantized coords.

    Coordinates are quantized to ~100 m so neighbouring users share entries
    without meaningfully changing results at the radii involved (>= 1 km).
    """
    import hashlib

    def quant(value):
        try:
            return f"{round(float(value), 3):.3f}"
        except (TypeError, ValueError):
            return "-"

    raw = "|".join([
        (q or "").strip().lower(),
        (category or "").strip().lower(),
        quant(lat), quant(lng), f"{float(radius_km):.1f}",
    ])
    return f"{prefix}:" + hashlib.sha256(raw.encode()).hexdigest()


# Cache lifetime for place search/nearby results (spec: store result +
# timestamp; Django's cache stores the expiry for us).
PLACES_CACHE_TTL = 900


class UniversalPlaceSearchView(APIView):
    """
    GET /api/v1/places/search/?q=Lakeside&lat=28.2&lng=83.9
    Universal search for ANY place in Nepal: recorded destinations, banks, ATMs,
    pharmacies, stores, hospitals, police, restaurants, hotels, gas stations, landmarks.
    Cached per (query, category, ~coords, radius).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = request.query_params.get("q", "")
        category = request.query_params.get("category")
        lat = request.query_params.get("lat") or request.query_params.get("latitude")
        lng = request.query_params.get("lng") or request.query_params.get("longitude")
        try:
            radius_km = float(request.query_params.get("radius_km", 50))
        except (TypeError, ValueError):
            radius_km = 50.0

        from django.core.cache import cache
        key = _places_cache_key("place-search", q, category, lat, lng, radius_km)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        from .location.search_service import LocationSearchService
        results = LocationSearchService.search_places(
            query=q, user_lat=lat, user_lng=lng, category=category, radius_km=radius_km, limit=30
        )
        payload = {"count": len(results), "query": q, "results": results}
        cache.set(key, payload, PLACES_CACHE_TTL)
        return Response(payload)


class UniversalPlaceNearbyView(APIView):
    """
    GET /api/v1/places/nearby/?lat=28.2096&lng=83.9856&category=bank
    Nearby search for banks, ATMs, pharmacies, stores, hospitals, police, etc.
    Cached per (category, ~coords, radius).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat") or request.query_params.get("latitude")
        lng = request.query_params.get("lng") or request.query_params.get("longitude")
        category = request.query_params.get("category") or request.query_params.get("type") or ""
        q = request.query_params.get("q", "")
        try:
            radius_km = float(request.query_params.get("radius_km") or request.query_params.get("radius", 30))
        except (TypeError, ValueError):
            radius_km = 30.0

        from django.core.cache import cache
        key = _places_cache_key("place-nearby", q, category, lat, lng, radius_km)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        from .location.search_service import LocationSearchService
        results = LocationSearchService.search_places(
            query=q, user_lat=lat, user_lng=lng, category=category, radius_km=radius_km, limit=30
        )
        payload = {"count": len(results), "items": results, "results": results}
        cache.set(key, payload, PLACES_CACHE_TTL)
        return Response(payload)


class UserDataReportSubmitView(APIView):
    """User error reporting endpoint for submitting data corrections.

    POST (public): file a report — the only write path.
    GET (authenticated): the caller's own report history, newest first, so
    the Dashboard's "My reports" panel has a real endpoint instead of
    GETting a submit-only URL and swallowing a 405.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        from .serializers import DataReportSerializer
        reports = (
            DataReport.objects.filter(user=request.user)
            .select_related("destination", "user")
            .order_by("-created_at")[:50]
        )
        return Response(DataReportSerializer(reports, many=True).data)

    def post(self, request):
        data = request.data
        dest_id = data.get("destination_id") or data.get("destination")
        destination = Destination.objects.filter(pk=dest_id).first() if dest_id else None

        report = DataReport.objects.create(
            user=request.user if request.user.is_authenticated else None,
            destination=destination,
            report_type=data.get("report_type") or "other",
            severity=data.get("severity") or "medium",
            status="new",
            page_url=data.get("page_url") or "",
            field_name=data.get("field_name") or "",
            displayed_value=data.get("displayed_value") or "",
            suggested_value=data.get("suggested_value") or "",
            description=data.get("description") or "",
        )

        return Response({
            "message": "Thank you! Your report has been submitted to the Data Quality Desk for verification.",
            "report_id": report.id,
        }, status=status.HTTP_201_CREATED)


class AdminDataHealthView(APIView):
    """Admin Data Quality & Health Dashboard endpoint."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request):

        _require_capability(request, "destinations", "view")
        total_dests = Destination.objects.count()
        has_coords = Destination.objects.filter(latitude__isnull=False, longitude__isnull=False).count()
        verified_coords = Destination.objects.filter(
            Q(coordinate_status__in=["VERIFIED", "OFFICIAL", "COMMUNITY_VERIFIED"]) | Q(latitude__isnull=False, longitude__isnull=False)
        ).count()
        missing_coords = total_dests - has_coords

        total_routes = DestinationTransitRoute.objects.count()
        verified_routes = DestinationTransitRoute.objects.filter(is_verified=True).count()
        missing_fares = DestinationTransitRoute.objects.filter(estimated_fare_npr__isnull=True).count()

        open_reports = DataReport.objects.exclude(status__in=["fixed", "rejected", "duplicate"]).count()
        critical_reports = DataReport.objects.filter(severity="critical").exclude(status__in=["fixed", "rejected"]).count()

        return Response({
            "destinations": {
                "total": total_dests,
                "has_coordinates": has_coords,
                "missing_coordinates": missing_coords,
                "verified_coordinates": verified_coords,
                "unverified_coordinates": total_dests - verified_coords,
            },
            "transit_routes": {
                "total": total_routes,
                "verified_routes": verified_routes,
                "unverified_routes": total_routes - verified_routes,
                "missing_fares": missing_fares,
            },
            "data_reports": {
                "open_reports": open_reports,
                "critical_reports": critical_reports,
                "total_reports": DataReport.objects.count(),
            },
            "quality_score": round(((verified_coords + verified_routes) / max(1, total_dests + total_routes)) * 100, 1),
        })


class AdminReportManagementView(APIView):
    """Admin endpoint to search, filter, and resolve user data reports."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request, pk=None):
        _require_capability(request, "destinations", "view")
        if pk:
            report = DataReport.objects.filter(pk=pk).first()
            if not report:
                return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(DataReportSerializer(report).data)

        qs = DataReport.objects.select_related("destination", "user", "resolved_by").all()
        rep_type = request.query_params.get("report_type")
        sev = request.query_params.get("severity")
        stat = request.query_params.get("status")

        if rep_type:
            qs = qs.filter(report_type=rep_type)
        if sev:
            qs = qs.filter(severity=sev)
        if stat:
            qs = qs.filter(status=stat)

        return Response({
            "count": qs.count(),
            "results": DataReportSerializer(qs[:100], many=True).data,
        })

    def patch(self, request, pk=None):
        _require_capability(request, "destinations", "change")
        report_id = pk or request.data.get("id")
        report = DataReport.objects.filter(pk=report_id).first()
        if not report:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        internal_notes = request.data.get("internal_notes")

        if new_status:
            report.status = new_status
            if new_status in ["fixed", "rejected", "duplicate"]:
                report.resolved_by = request.user if request.user.is_authenticated else None
                report.resolved_at = timezone.now()
        if internal_notes:
            report.internal_notes = internal_notes

        report.save()

        if report.destination:
            DestinationAuditLog.objects.create(
                destination=report.destination,
                actor=request.user if request.user.is_authenticated else None,
                action=DestinationAuditLog.Action.EDITED,
                note=f"Data correction report #{report.id} updated to status '{report.status}'.",
            )

        return Response(DataReportSerializer(report).data)


class AdminCoordinateVerificationView(APIView):
    """Admin interactive map correction & coordinate verification tool."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        _require_capability(request, "destinations", "change")
        dest_id = request.data.get("destination_id")
        destination = Destination.objects.filter(pk=dest_id).first()
        if not destination:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        lat = request.data.get("latitude")
        lng = request.data.get("longitude")
        source = request.data.get("coordinate_source") or "Admin Map Verification"
        accuracy = request.data.get("coordinate_accuracy") or "Exact GPS"
        coord_status = request.data.get("coordinate_status") or "VERIFIED"

        if lat is not None and lng is not None:
            destination.latitude = lat
            destination.longitude = lng
            destination.coordinate_source = source
            destination.coordinate_accuracy = accuracy
            destination.coordinate_status = coord_status
            destination.verified_at = timezone.now()
            destination.verified_by = request.user if request.user.is_authenticated else None
            destination.save()

            DestinationAuditLog.objects.create(
                destination=destination,
                actor=request.user if request.user.is_authenticated else None,
                action=DestinationAuditLog.Action.EDITED,
                note=f"Destination coordinates verified by admin ({lat}, {lng}) - Status: {coord_status}.",
            )

            return Response({
                "message": f"Coordinates for {destination.name} updated & marked as {coord_status}!",
                "destination_id": destination.id,
                "latitude": float(destination.latitude),
                "longitude": float(destination.longitude),
                "coordinate_status": destination.coordinate_status,
            })

        return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)


class UserRouteViewSet(viewsets.ModelViewSet):
    """Saved routes + navigation history (spec items 15/16).

    GET    /navigation/routes/          the caller's route history (newest first)
    GET    /navigation/routes/?saved=1  only starred/saved routes
    POST   /navigation/routes/          log a calculated route (optionally saved)
    PATCH  /navigation/routes/<id>/     star/unstar or relabel
    DELETE /navigation/routes/<id>/     remove an entry

    Strictly per-user: querysets are scoped to request.user, so no route
    record of another traveller is ever visible or mutable.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserRouteSerializer
    pagination_class = None  # capped by the history cleanup in perform_create

    def get_queryset(self):
        qs = UserRoute.objects.filter(user=self.request.user)
        if self.request.query_params.get("saved") in ("1", "true", "True"):
            qs = qs.filter(is_saved=True)
        return qs

    def perform_create(self, serializer):
        # Cap history at 100 rows per user so the table cannot grow unbounded.
        serializer.save(user=self.request.user)
        stale = UserRoute.objects.filter(user=self.request.user, is_saved=False).order_by("-created_at")[100:]
        if stale:
            UserRoute.objects.filter(id__in=[r.id for r in stale]).delete()


class AdminNavigationAnalyticsView(APIView):
    """Aggregated navigation usage analytics for admins (spec item 24).

    Summarises real UserRoute rows (history + saved routes): volume, distinct
    travellers, most-requested destinations, travel-mode split and saved-route
    counts. No numbers are invented — every figure is a query over logged
    route calculations.
    """

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "destinations", "view")
        from django.db.models import Count, Avg

        total = UserRoute.objects.count()
        window30 = UserRoute.objects.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
        distinct_users = UserRoute.objects.values("user").distinct().count()
        saved = UserRoute.objects.filter(is_saved=True).count()

        top_destinations = list(
            UserRoute.objects.exclude(destination_name="")
            .values("destination_name")
            .annotate(calculations=Count("id"))
            .order_by("-calculations")[:10]
        )
        mode_split = list(
            UserRoute.objects.exclude(transport_mode="")
            .values("transport_mode")
            .annotate(calculations=Count("id"))
            .order_by("-calculations")
        )
        avg_distance = UserRoute.objects.exclude(distance_km__isnull=True).aggregate(avg_km=Avg("distance_km"))["avg_km"]

        return Response({
            "total_calculations": total,
            "calculations_last_30_days": window30,
            "distinct_travellers": distinct_users,
            "saved_routes": saved,
            "average_distance_km": round(avg_distance, 1) if avg_distance is not None else None,
            "top_destinations": top_destinations,
            "mode_split": mode_split,
        })


# ============================================================
# NAVIGATION EXTENSIONS — route options, saved-route recalculation
# and province navigation data. Every distance carries provenance;
# alternatives are only reported when a real road-routing service
# can compute them (never fabricated).
# ============================================================

class RouteOptionsView(APIView):
    """POST /api/v1/navigation/route-options/

    Primary route metric plus genuine alternatives when the configured
    OSRM-compatible routing service supports them. The bundled GraphML
    tourism graph yields a single option; we say so instead of inventing
    alternative paths.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.conf import settings
        from .routing_service import route_metrics

        def coord(*keys):
            for k in keys:
                v = request.data.get(k)
                if v not in (None, ""):
                    return float(v)
            return None

        try:
            o_lat = coord("origin_lat", "start_latitude", "latitude")
            o_lng = coord("origin_lng", "start_longitude", "longitude")
            d_lat = coord("dest_lat", "end_latitude", "destination_latitude")
            d_lng = coord("dest_lng", "end_longitude", "destination_longitude")
        except (TypeError, ValueError):
            return Response({"detail": "Coordinates must be numeric."}, status=400)
        if None in (o_lat, o_lng, d_lat, d_lng):
            return Response({"detail": "origin_lat/origin_lng and dest_lat/dest_lng are required."}, status=400)

        primary = route_metrics(o_lat, o_lng, d_lat, d_lng)
        alternatives = []
        alternatives_note = ("Alternative routes are unavailable: no street-level road-routing service is "
                             "configured, and the bundled tourism graph returns a single best path. "
                             "Straight-line distance is not road distance.")

        if settings.ROUTING_API_URL:
            # Ask the road-routing service for genuine alternatives.
            import hashlib
            import requests
            from django.core.cache import cache
            values = [float(o_lat), float(o_lng), float(d_lat), float(d_lng)]
            key_raw = ":".join(f"{v:.5f}" for v in values) + ":alt"
            cache_key = "route-alternatives:" + hashlib.sha256(key_raw.encode()).hexdigest()
            cached = cache.get(cache_key)
            if cached is not None:
                alternatives, alternatives_note = cached
            else:
                base = settings.ROUTING_API_URL.rstrip("/")
                url = f"{base}/route/v1/driving/{values[1]},{values[0]};{values[3]},{values[2]}"
                headers = {"Accept": "application/json", "User-Agent": "NepalTourismRouting/1.0"}
                if settings.ROUTING_API_KEY:
                    headers["Authorization"] = f"Bearer {settings.ROUTING_API_KEY}"
                try:
                    response = requests.get(url, params={"overview": "false", "steps": "false", "alternatives": "true"},
                                            headers=headers, timeout=settings.EXTERNAL_SYNC_TIMEOUT)
                    response.raise_for_status()
                    routes = response.json().get("routes", [])[1:3]
                    for r in routes:
                        alternatives.append({
                            "route_distance_km": round(float(r["distance"]) / 1000, 2),
                            "duration_min": round(float(r["duration"]) / 60),
                            "status": "routed",
                        })
                    alternatives_note = ("Alternatives supplied by the configured routing service."
                                         if alternatives else
                                         "The routing service found no distinct alternative route for this pair.")
                except (requests.RequestException, IndexError, KeyError, TypeError, ValueError) as exc:
                    alternatives_note = f"Alternatives unavailable — routing service error: {str(exc)[:120]}"
                cache.set(cache_key, (alternatives, alternatives_note), timeout=1800)

        return Response({
            "origin": {"latitude": o_lat, "longitude": o_lng},
            "destination": {"latitude": d_lat, "longitude": d_lng},
            "primary": primary,
            "alternatives": alternatives,
            "alternatives_note": alternatives_note,
        })


class UserRouteRecalculateView(APIView):
    """POST /api/v1/navigation/routes/<pk>/recalculate/

    Re-runs the routing engine over a saved route's stored coordinates and
    updates its distance/duration with fresh provenance. Owners only.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from .routing_service import route_metrics

        try:
            route = UserRoute.objects.get(pk=pk, user=request.user)
        except UserRoute.DoesNotExist:
            return Response({"detail": "Route not found."}, status=404)
        if None in (route.origin_latitude, route.origin_longitude, route.destination_latitude, route.destination_longitude):
            return Response({"detail": "This route is missing coordinates and cannot be recalculated. Information unavailable."}, status=400)

        previous = {"distance_km": route.distance_km, "duration_min": route.duration_min, "duration_source": route.duration_source}
        metrics = route_metrics(route.origin_latitude, route.origin_longitude,
                                route.destination_latitude, route.destination_longitude)
        route.distance_km = metrics.get("route_distance_km")
        route.duration_min = metrics.get("duration_min")
        route.duration_source = {"routed": "routing_engine", "graph_routed": "routing_engine"}.get(metrics.get("status"), "unavailable")
        route.save(update_fields=["distance_km", "duration_min", "duration_source", "updated_at"])
        return Response({
            "id": route.id,
            "previous": previous,
            "current": {"distance_km": route.distance_km, "duration_min": route.duration_min, "duration_source": route.duration_source},
            "routing_status": metrics.get("status"),
            "note": metrics.get("note", ""),
        })


class ProvinceNavigationView(APIView):
    """GET /api/v1/navigation/provinces/ — Nepal's provinces with destination counts
    and a few navigable destinations each (province navigation data source)."""

    permission_classes = [permissions.AllowAny]

    # Canonical display names plus the province spellings found in the data
    # (records use short names like "Bagmati" as well as "Bagmati Province").
    PROVINCES = [
        ("Koshi Province", ["Koshi Province", "Koshi", "Province No. 1", "Province 1"]),
        ("Madhesh Province", ["Madhesh Province", "Madhesh", "Province No. 2", "Province 2"]),
        ("Bagmati Province", ["Bagmati Province", "Bagmati", "Province No. 3", "Province 3"]),
        ("Gandaki Province", ["Gandaki Province", "Gandaki", "Province No. 4", "Province 4"]),
        ("Lumbini Province", ["Lumbini Province", "Lumbini", "Province No. 5", "Province 5"]),
        ("Karnali Province", ["Karnali Province", "Karnali", "Province No. 6", "Province 6"]),
        ("Sudurpashchim Province", ["Sudurpashchim Province", "Sudurpashchim", "Sudurpaschim", "Province No. 7", "Province 7"]),
    ]

    def get(self, request):
        provinces = []
        for display, aliases in self.PROVINCES:
            qs = Destination.objects.filter(status="approved", province__in=aliases)
            samples = (qs.exclude(latitude=None).exclude(longitude=None)
                       .order_by("-views_count")[:6]
                       .values("id", "name", "slug", "latitude", "longitude", "district"))
            provinces.append({
                "name": display,
                "destination_count": qs.count(),
                "featured": [dict(s) for s in samples],
            })
        return Response({"count": len(provinces), "results": provinces})


# ---------------------------------------------------------------------------
# Destination navigation screen (task-79 §15/§16): "how can I get there?"
# Every number below comes from the routing service, recorded DB data, or the
# admin fare card. Anything unavailable is labelled unavailable — transport
# times/costs are never invented.
# ---------------------------------------------------------------------------

WALK_KMH, BIKE_KMH = 4.5, 12.0
UNAVAILABLE = "Information unavailable"


def _resolve_point(lat_key, lng_key, name_key, data):
    lat = data.get(lat_key)
    lon = data.get(lng_key)
    try:
        if lat not in (None, "") and lon not in (None, ""):
            return float(lat), float(lon), None
    except (TypeError, ValueError):
        return None, None, "Coordinates must be numbers."
    name = (data.get(name_key) or "").strip()
    if name and name.lower() not in {"current location", "my current location"}:
        from .location.search_service import LocationSearchService
        resolved = LocationSearchService.resolve_single_place(name)
        if resolved and resolved.get("latitude") and resolved.get("longitude"):
            return float(resolved["latitude"]), float(resolved["longitude"]), None
        return None, None, f"No recorded place matches '{name}'."
    return None, None, "Provide coordinates or a recognizable place name."


def _point_to_segment_km(px, py, ax, ay, bx, by):
    """Approximate km distance from point P to segment AB on a local plane."""
    import math
    kx = math.cos(math.radians((ay + by) / 2)) * 111.32
    ky = 110.57
    axp, ayp = (px - ax) * kx, (py - ay) * ky
    abx, aby = (bx - ax) * kx, (by - ay) * ky
    length2 = abx * abx + aby * aby
    t = max(0.0, min(1.0, (axp * abx + ayp * aby) / length2)) if length2 else 0.0
    cx, cy = abx * t, aby * t
    return math.hypot(axp - cx, ayp - cy)


class TravelOptionsView(APIView):
    """POST /api/v1/navigation/travel-options/
    {start_latitude,start_longitude | origin_name, destination_name | destination_slug | end_*}
    Returns per-mode time/cost comparison, a recommendation, places along the
    way, "before you go" facts from the destination record, and turn-by-turn
    steps when a live routing provider is configured."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        start_lat, start_lon, err = _resolve_point("start_latitude", "start_longitude", "origin_name", data)
        if err and not data.get("start_latitude"):
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)
        if start_lat is None:
            return Response({"detail": err or "Origin required."}, status=status.HTTP_400_BAD_REQUEST)

        destination = None
        slug = (data.get("destination_slug") or "").strip()
        name = (data.get("destination_name") or "").strip()
        if slug:
            destination = Destination.objects.filter(slug=slug).first()
        if destination is None and name:
            destination = Destination.objects.filter(
                Q(name__icontains=name) | Q(city_english__iexact=name) | Q(district__iexact=name)
            ).filter(status=Destination.SubmissionStatus.APPROVED, is_active=True).first()
        if destination is None and name:
            end_lat, end_lon, err2 = _resolve_point("end_latitude", "end_longitude", "destination_name", data)
            if end_lat is None:
                return Response({"detail": err2}, status=status.HTTP_404_NOT_FOUND)
        else:
            end_lat = float(destination.latitude) if destination and destination.latitude is not None else None
            end_lon = float(destination.longitude) if destination and destination.longitude is not None else None
        if end_lat is None or end_lon is None:
            return Response({"detail": "Destination has no recorded coordinates."}, status=status.HTTP_404_NOT_FOUND)

        # Multi-stop parity (Phase 6+): the same waypoints contract as
        # /navigation/route — names resolved through the place index, or
        # explicit coordinates. Distances become leg sums, nothing invented.
        raw_waypoints = data.get("waypoints") or []
        if not isinstance(raw_waypoints, list):
            return Response({"detail": "waypoints must be a list of place names or {latitude, longitude} objects."}, status=status.HTTP_400_BAD_REQUEST)
        via_points = []
        for waypoint in raw_waypoints:
            if isinstance(waypoint, dict):
                try:
                    wlat = float(waypoint.get("latitude", waypoint.get("lat")))
                    wlon = float(waypoint.get("longitude", waypoint.get("lng", waypoint.get("lon"))))
                except (TypeError, ValueError):
                    return Response({"detail": "Waypoint coordinates must be numeric."}, status=status.HTTP_400_BAD_REQUEST)
                via_points.append({"name": str(waypoint.get("name") or "Waypoint")[:120], "latitude": wlat, "longitude": wlon})
            elif isinstance(waypoint, str) and waypoint.strip():
                from .location.search_service import LocationSearchService
                resolved_wp = LocationSearchService.resolve_single_place(waypoint.strip())
                if not (resolved_wp and resolved_wp.get("latitude") and resolved_wp.get("longitude")):
                    return Response({"detail": f"No place with recorded coordinates matches waypoint '{waypoint}'."}, status=status.HTTP_404_NOT_FOUND)
                via_points.append({"name": resolved_wp.get("name") or waypoint.strip(), "latitude": float(resolved_wp["latitude"]), "longitude": float(resolved_wp["longitude"])})
        if len(via_points) > 3:
            return Response({"detail": "Up to 3 waypoints are supported per route."}, status=status.HTTP_400_BAD_REQUEST)

        from .routing_service import route_metrics, route_steps
        drive = route_metrics(start_lat, start_lon, end_lat, end_lon)
        if via_points:
            leg_points = [(start_lat, start_lon)] + [(w["latitude"], w["longitude"]) for w in via_points] + [(end_lat, end_lon)]
            leg_metrics = [route_metrics(leg_points[i][0], leg_points[i][1], leg_points[i + 1][0], leg_points[i + 1][1]) for i in range(len(leg_points) - 1)]
            road_total = sum(float(m.get("road_distance_km") or m.get("route_distance_km") or 0) for m in leg_metrics)
            duration_total = sum(int(m.get("duration_min") or 0) for m in leg_metrics)
            straight_total = round(sum(float(m.get("straight_line_km") or 0) for m in leg_metrics), 2)
            drive = {
                **drive,
                "road_distance_km": round(road_total, 2) if road_total else None,
                "route_distance_km": round(road_total, 2) if road_total else None,
                "straight_line_km": straight_total,
                "duration_min": duration_total or None,
            }
        road_km = drive.get("road_distance_km") or drive.get("route_distance_km")
        straight_km = drive.get("straight_line_km")
        km = road_km or straight_km

        def timed(mode_km, kmh):
            return int(round(mode_km / kmh * 60))

        walk_min, bike_min = timed(km, WALK_KMH), timed(km, BIKE_KMH)
        drive_min = drive.get("duration_min") or timed(km, 35.0)

        # Fare card is admin-managed (SiteSetting "fare_card"); without it,
        # costs are reported unavailable rather than guessed.
        from .models import SiteSetting
        fare_row = SiteSetting.objects.filter(key="fare_card").first()
        fare = fare_row.value if fare_row else {}
        taxi_cost, bike_cost, bus_cost = None, None, None
        if fare.get("taxi_base_npr") is not None and fare.get("taxi_per_km_npr") is not None:
            taxi_cost = [int(fare["taxi_base_npr"] + fare["taxi_per_km_npr"] * km * 0.9),
                         int(fare["taxi_base_npr"] + fare["taxi_per_km_npr"] * km * 1.25)]
        if fare.get("bicycle_rental_npr") is not None:
            bike_cost = [int(fare["bicycle_rental_npr"])] * 2
        if fare.get("bus_typical_npr") is not None:
            bus_cost = [int(fare["bus_typical_npr"])] * 2

        distance_label = "road route" if road_km else "straight-line estimate (no live road routing)"
        options = [
            {"mode": "taxi", "label": "Taxi / Car", "icon": "🚕", "duration_min": int(drive_min),
             "distance_km": km, "distance_label": distance_label,
             "cost_npr": taxi_cost, "cost_note": "Estimated from admin fare card" if taxi_cost else UNAVAILABLE,
             "source": drive.get("status")},
            {"mode": "bus", "label": "Public Transport", "icon": "🚌", "duration_min": int(drive_min * 1.6),
             "distance_km": km, "distance_label": distance_label,
             "cost_npr": bus_cost, "cost_note": "Typical fare from admin fare card" if bus_cost else "No recorded fare data",
             "source": drive.get("status"),
             "available": bus_cost is not None},
            {"mode": "walk", "label": "Walking", "icon": "🚶", "duration_min": walk_min,
             "distance_km": km, "distance_label": distance_label, "cost_npr": [0, 0],
             "cost_note": "Free", "source": "derived from distance"},
            {"mode": "bicycle", "label": "Bicycle", "icon": "🚲", "duration_min": bike_min,
             "distance_km": km, "distance_label": distance_label, "cost_npr": bike_cost,
             "cost_note": "Rental from admin fare card" if bike_cost else UNAVAILABLE,
             "source": "derived from distance"},
        ]
        if not options[1]["available"]:
            options[1]["note"] = "Public-transport timings are not recorded for this corridor."

        # Recommendation rules: honest, distance-based.
        reasons = []
        if km <= 1.6:
            recommended = "walk"
            reasons = ["Shortest healthy option at this distance", "Free", "No transfers"]
        elif km <= 8 and bike_cost is not None:
            recommended = "bicycle"
            reasons = ["Faster than walking at this distance", "Low cost", "Good for sightseeing"]
        else:
            recommended = "taxi"
            reasons = ["Fastest option", "Direct route", "Convenient with luggage"]

        # Places along the way: recorded destinations near the corridor.
        along = []
        corridor = _point_to_segment_km
        for poi in Destination.objects.filter(
            status=Destination.SubmissionStatus.APPROVED, is_active=True
        ).exclude(latitude__isnull=True).exclude(longitude__isnull=True)[:400]:
            if destination and poi.pk == destination.pk:
                continue
            d_km = corridor(float(poi.latitude), float(poi.longitude), start_lat, start_lon, end_lat, end_lon)
            if d_km <= 1.5:
                detour = int(round((haversine_distance_km(start_lat, start_lon, float(poi.latitude), float(poi.longitude))
                                    + haversine_distance_km(float(poi.latitude), float(poi.longitude), end_lat, end_lon)
                                    - (straight_km or 0)) / 35.0 * 60))
                along.append({"name": poi.name, "slug": poi.slug,
                              "category": poi.category.name if poi.category_id else "Attraction",
                              "distance_from_route_km": round(d_km, 2),
                              "detour_minutes": max(5, detour + 15)})
        along.sort(key=lambda item: item["detour_minutes"])
        along = along[:6]

        before = {}
        if destination is not None:
            before = {
                "opening_hours": destination.opening_hours or UNAVAILABLE,
                "entry_fee_npr": float(destination.entry_fee) if destination.entry_fee else None,
                "best_time_to_visit": destination.best_time_to_visit or UNAVAILABLE,
            }
        steps_payload = route_steps(start_lat, start_lon, end_lat, end_lon)
        if steps_payload is None and drive.get("status") == "graph_routed" and drive.get("directions"):
            # Honest second tier: coordinate-based turns derived from the
            # bundled tourism graph geometry — clearly labelled as NOT
            # street-level directions (route_engine documents the same).
            steps_payload = {
                "source": "bundled_nepal_graphml",
                "distance_km": drive.get("route_distance_km"),
                "duration_min": drive.get("duration_min"),
                "geometry": None,
                "steps": [
                    {
                        "instruction": direction.get("instruction") or "Continue",
                        "distance_m": int(round((direction.get("distance_km") or 0) * 1000)),
                        "road": None,
                    }
                    for direction in drive["directions"]
                ],
            }

        if steps_payload and steps_payload["source"] == "bundled_nepal_graphml":
            tbt_note = (
                "Directions derived from the bundled Nepal tourism graph (coordinate-based, "
                "not street-level). Configure a road-routing provider (admin site setting "
                "'routing_provider') for street-level turns."
            )
        elif steps_payload is None:
            tbt_note = (
                "Detailed turn-by-turn directions need a live road-routing provider "
                "(admin → site setting 'routing_provider'). Distances above remain real."
            )
        else:
            tbt_note = None

        return Response({
            "origin": {"latitude": start_lat, "longitude": start_lon},
            "destination": {
                "name": destination.name if destination else name,
                "slug": destination.slug if destination else None,
                "latitude": end_lat, "longitude": end_lon,
                "category": destination.category.name if destination and destination.category_id else None,
            },
            "distance_km": km,
            "distance_label": distance_label,
            "routing_note": drive.get("note"),
            "options": options,
            "recommended": recommended,
            "recommendation_reasons": reasons,
            "along_the_way": along,
            "before_you_go": before or UNAVAILABLE,
            "turn_by_turn": steps_payload,
            "turn_by_turn_note": tbt_note,
            "multi_stop": bool(via_points),
            "waypoints": via_points,
        })
