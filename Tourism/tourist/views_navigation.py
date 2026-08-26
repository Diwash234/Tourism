import math
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import (
    Destination, DestinationTransitRoute, RouteSegment, DataReport,
    DestinationAuditLog,
)
from .serializers import (
    DestinationTransitRouteSerializer, RouteSegmentSerializer, DataReportSerializer,
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
    Calculates journey from a real user origin to a real destination.
    NEVER defaults to Kathmandu unless Kathmandu is explicitly specified as origin.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        dest_slug = data.get("destination_slug") or data.get("destination")
        dest_id = data.get("destination_id")

        destination = None
        if dest_id:
            destination = Destination.objects.filter(pk=dest_id).first()
        elif dest_slug:
            destination = Destination.objects.filter(Q(slug=dest_slug) | Q(id=dest_slug if str(dest_slug).isdigit() else 0)).first()

        if not destination:
            return Response({"detail": "Destination record not found."}, status=status.HTTP_404_NOT_FOUND)

        origin_name = (data.get("origin_name") or data.get("origin") or "").strip()
        origin_lat = data.get("origin_lat") or data.get("latitude")
        origin_lng = data.get("origin_lng") or data.get("longitude")
        transport_mode = data.get("transport_mode") or "Private Car / Taxi"

        # Check destination coordinates availability
        dest_has_coords = bool(destination.latitude is not None and destination.longitude is not None)

        if not dest_has_coords:
            return Response({
                "destination_id": destination.id,
                "destination_name": destination.name,
                "destination_slug": destination.slug,
                "has_coordinates": False,
                "origin_name": origin_name or "Selected Starting Point",
                "distance_km": None,
                "estimated_duration": "Route unavailable",
                "fare_npr": None,
                "fare_status": "Fare unavailable",
                "route_status": "Map location unavailable — GPS coordinates not yet verified",
                "confidence_level": "UNKNOWN",
                "segments": [],
            })

        # Calculate coordinates-based distance if origin lat/lng provided
        distance_km = None
        duration_mins = None
        confidence = "ESTIMATED"

        if origin_lat is not None and origin_lng is not None:
            raw_dist = haversine_distance_km(origin_lat, origin_lng, destination.latitude, destination.longitude)
            if raw_dist is not None:
                # Multiply by 1.35 for Nepal mountain road curvature
                distance_km = round(raw_dist * 1.35, 1)
                # Average mountain driving speed ~35 km/h
                duration_hours = distance_km / 35.0
                duration_mins = int(duration_hours * 60)
                confidence = "CALCULATED"

        # Check DB for matching verified route from origin
        db_route = None
        if origin_name:
            db_route = DestinationTransitRoute.objects.filter(
                destination=destination,
                origin__icontains=origin_name,
                is_active=True,
            ).first()

        if not db_route:
            db_route = DestinationTransitRoute.objects.filter(
                destination=destination,
                is_active=True,
            ).first()

        fare_npr = None
        fare_status = "Fare not recorded"
        fare_source = "Unverified"

        if db_route:
            if db_route.distance_km and not distance_km:
                distance_km = float(db_route.distance_km)
            if db_route.estimated_fare_npr:
                fare_npr = float(db_route.estimated_fare_npr)
                fare_status = "Verified Fare" if db_route.is_verified else "Recorded Estimate"
                fare_source = db_route.route_source or "Transport Authority"
                confidence = db_route.confidence_level

        # Format duration string
        duration_str = "Travel time unavailable"
        if duration_mins:
            hrs = duration_mins // 60
            mins = duration_mins % 60
            if hrs > 0:
                duration_str = f"{hrs}h {mins}m" if mins > 0 else f"{hrs} hours"
            else:
                duration_str = f"{mins} mins"
        elif db_route and db_route.approx_duration:
            duration_str = db_route.approx_duration

        # Fetch multi-leg segments if available
        segments = []
        if db_route:
            seg_qs = db_route.segments.all()
            if seg_qs.exists():
                segments = RouteSegmentSerializer(seg_qs, many=True).data

        return Response({
            "destination_id": destination.id,
            "destination_name": destination.name,
            "destination_slug": destination.slug,
            "has_coordinates": True,
            "destination_latitude": float(destination.latitude),
            "destination_longitude": float(destination.longitude),
            "origin_name": origin_name or "Current Location",
            "origin_latitude": float(origin_lat) if origin_lat is not None else None,
            "origin_longitude": float(origin_lng) if origin_lng is not None else None,
            "transport_mode": db_route.transport_mode if db_route else transport_mode,
            "distance_km": distance_km if distance_km is not None else "Distance unavailable",
            "estimated_duration": duration_str,
            "fare_npr": fare_npr,
            "fare_currency": "NPR",
            "fare_status": fare_status,
            "fare_source": fare_source,
            "confidence_level": confidence,
            "route_status": "Route calculated for origin",
            "calculated_at": timezone.now().isoformat(),
            "segments": segments,
        })


class UserDataReportSubmitView(APIView):
    """User error reporting endpoint for submitting data corrections."""
    permission_classes = [permissions.AllowAny]

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
