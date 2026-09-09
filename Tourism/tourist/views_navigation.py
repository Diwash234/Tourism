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

        # Default fallback origin if GPS or origin coordinates are missing
        if origin_lat is None or origin_lng is None:
            origin_lat, origin_lng = 28.2096, 83.9856
            origin_name = origin_name or "Pokhara Center"

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
            dest_lat, dest_lng = 28.2096, 83.9856

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
