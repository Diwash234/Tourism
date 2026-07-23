"""
Compatibility layer: thin views matching URL paths, HTTP methods, and
query-param names your frontend already calls (recommendationApi.js,
budgetApi.js, alertApi.js, nearbyApi.js, navigation route caller), so it
works without a rewrite. Each one just delegates to the real logic that
already exists elsewhere (utils.py, EmergencyContact/Budget models).

If your frontend's param names differ from what's implemented here, tell
me the exact request (as seen in DevTools) and I'll adjust these to match.
"""
from decimal import Decimal, InvalidOperation

from django.db.models import Sum, Count
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Budget, EmergencyContact
from .serializers import DestinationListSerializer, EmergencyContactSerializer
from .utils import get_ml_recommendations, get_ml_best_route, haversine_distance


def _parse_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' must be a number.")


class RecommendationsPersonalizedView(APIView):
    """
    GET /api/v1/recommendations/personalized?latitude=&longitude=&lat=&lng=&top_n=
    Alias for POST /api/v1/ml/recommendations/ — same underlying logic
    (falls back to top-rated destinations if the ML service is down), just
    reachable via GET + query params to match the frontend's existing call.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get("latitude") or request.query_params.get("lat")
        lon = request.query_params.get("longitude") or request.query_params.get("lng")
        top_n = int(request.query_params.get("top_n", 5))

        if lat is None and request.user.is_authenticated:
            lat, lon = request.user.latitude, request.user.longitude

        recommendations = get_ml_recommendations(user=request.user, latitude=lat, longitude=lon, top_n=top_n)

        from .models import Destination

        if recommendations:
            ordered_ids = [r["destination_id"] for r in recommendations]
            score_by_id = {r["destination_id"]: r.get("score") for r in recommendations}
            destinations = list(
                Destination.objects.filter(
                    id__in=ordered_ids, is_active=True, status=Destination.SubmissionStatus.APPROVED
                )
            )
            destinations.sort(key=lambda d: ordered_ids.index(d.id))
            source = "ml_service"
        else:
            destinations = list(
                Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)
                .order_by("-average_rating")[:top_n]
            )
            score_by_id = {}
            source = "fallback_top_rated"

        context = {"request": request, "user_lat": lat, "user_lon": lon}
        results = DestinationListSerializer(destinations, many=True, context=context).data
        for item in results:
            item["ml_score"] = score_by_id.get(item["id"])

        return Response({"source": source, "results": results})


class BudgetSummaryView(APIView):
    """
    GET /api/v1/budget/summary
    Aggregate summary of the logged-in user's own Budget entries: total
    spent, count, and a breakdown by category. (Different from
    /api/v1/ml/budget/, which is a forward-looking ML *estimate* for a
    trip you haven't taken yet — this summarizes what you've already logged.)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Budget.objects.filter(user=request.user)
        total = qs.aggregate(total=Sum("amount"), count=Count("id"))
        by_category = list(
            qs.values("category").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")
        )
        return Response({
            "total_amount": total["total"] or 0,
            "entry_count": total["count"] or 0,
            "by_category": by_category,
        })


class EmergencyContactsCompatView(APIView):
    """
    GET /api/v1/emergency/contacts?lat=&lng=&radius_km=
    Alias for GET /api/v1/emergency-contacts/nearest/?latitude=&longitude=
    with the `lat`/`lng` param names your frontend already sends.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return _nearest_contacts_response(request, contact_type=None)


class NearbyHospitalsView(APIView):
    """GET /api/v1/nearby/hospitals?lat=&lng= — hospitals only, nearest first."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return _nearest_contacts_response(request, contact_type=EmergencyContact.ContactType.HOSPITAL)


class NearbyPoliceView(APIView):
    """GET /api/v1/nearby/police?lat=&lng= — police only, nearest first."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return _nearest_contacts_response(request, contact_type=EmergencyContact.ContactType.POLICE)


def _nearest_contacts_response(request, contact_type):
    try:
        lat = _parse_float(request.query_params.get("lat") or request.query_params.get("latitude"), "lat")
        lon = _parse_float(request.query_params.get("lng") or request.query_params.get("longitude"), "lng")
    except (ValueError, TypeError):
        return Response({"detail": "lat and lng query params are required."}, status=status.HTTP_400_BAD_REQUEST)
    radius_km = float(request.query_params.get("radius_km", 25))

    qs = EmergencyContact.objects.all()
    if contact_type:
        qs = qs.filter(contact_type=contact_type)

    nearest_by_type = {}
    for contact in qs:
        distance = haversine_distance(lat, lon, contact.latitude, contact.longitude)
        if distance > radius_km:
            continue
        current = nearest_by_type.get(contact.contact_type)
        if current is None or distance < current[0]:
            nearest_by_type[contact.contact_type] = (distance, contact)

    contacts = [c for _, c in sorted(nearest_by_type.values(), key=lambda pair: pair[0])]
    serializer = EmergencyContactSerializer(contacts, many=True, context={"request": request, "user_lat": lat, "user_lon": lon})
    return Response(serializer.data)


class NavigationRouteView(APIView):
    """
    POST /api/v1/navigation/route
    Alias for POST /api/v1/ml/best-route/, accepting a few common field
    name variants (startLat/startLng/endLat/endLng, start_latitude/..., or
    lat/lng pairs) so it works regardless of which convention your
    navigation caller uses. Tell me the exact body your frontend sends
    (DevTools -> Network -> this request -> Payload) if this still 400s,
    and I'll match it exactly.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data

        def pick(*keys):
            for key in keys:
                if key in data and data[key] not in (None, ""):
                    return data[key]
            return None

        try:
            start_lat = _parse_float(pick("start_latitude", "startLat", "start_lat", "originLat"), "start latitude")
            start_lon = _parse_float(pick("start_longitude", "startLng", "start_lng", "originLng"), "start longitude")
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Your Navigation.jsx sends `destination_name` (free text) rather
        # than raw coordinates — resolve it against real Destination rows
        # first. Match destination name, city, country or slug so queries like
        # "kathmandu" still work even when the user is searching by district/city.
        destination_obj = None
        destination_name = pick("destination_name", "destinationName")
        if destination_name:
            from .models import Destination

            candidates = Destination.objects.filter(
                Q(name__icontains=destination_name)
                | Q(city__icontains=destination_name)
                | Q(country__icontains=destination_name)
                | Q(slug__icontains=destination_name),
                is_active=True,
                status=Destination.SubmissionStatus.APPROVED,
            )
            if not candidates.exists():
                return Response(
                    {"detail": f"No destination found matching '{destination_name}'."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if start_lat is not None and start_lon is not None:
                destination_obj = min(
                    candidates,
                    key=lambda dest: haversine_distance(start_lat, start_lon, dest.latitude, dest.longitude),
                )
            else:
                destination_obj = candidates.first()
            end_lat, end_lon = destination_obj.latitude, destination_obj.longitude
        else:
            try:
                end_lat = _parse_float(pick("end_latitude", "endLat", "end_lat", "destinationLat"), "end latitude")
                end_lon = _parse_float(pick("end_longitude", "endLng", "end_lng", "destinationLng"), "end longitude")
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        result = get_ml_best_route(start_lat, start_lon, end_lat, end_lon)
        if result is None:
            return Response(
                {"detail": "Routing service is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_data = dict(result)
        response_data["route"] = result.get("path", [])  # alias matching Navigation.jsx's expected field name
        if destination_obj:
            response_data["destination"] = DestinationListSerializer(destination_obj, context={"request": request}).data
        return Response(response_data)


class WeatherByCoordinatesView(APIView):
    """
    GET /api/v1/weather/current/?lat=&lng=
    Generic coordinate-based weather lookup — an alias for the same
    OpenWeatherMap client used by /destinations/{slug}/weather/, for
    widgets (like a dashboard) that show "current weather at my location"
    rather than weather for one specific destination.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = _parse_float(request.query_params.get("lat") or request.query_params.get("latitude"), "lat")
            lon = _parse_float(request.query_params.get("lng") or request.query_params.get("longitude"), "lng")
        except (ValueError, TypeError):
            return Response({"detail": "lat and lng query params are required."}, status=status.HTTP_400_BAD_REQUEST)

        from .utils import get_current_weather

        result = get_current_weather(lat, lon)
        if result is None:
            return Response(
                {"detail": "Weather data is currently unavailable (check OPENWEATHER_API_KEY)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(result)


class NearbyPlacesCompatView(APIView):
    """
    GET /api/v1/nearby/places?lat=&lng=&radius=
    Alias combining your own Destination table (nearest-first, matching
    /destinations/nearby/) with raw OpenStreetMap tourism points, so a
    generic "what's around me" widget has something to show even for
    areas with no Destination rows yet.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = _parse_float(request.query_params.get("lat") or request.query_params.get("latitude"), "lat")
            lon = _parse_float(request.query_params.get("lng") or request.query_params.get("longitude"), "lng")
        except (ValueError, TypeError):
            return Response({"detail": "lat and lng query params are required."}, status=status.HTTP_400_BAD_REQUEST)
        radius_m = int(request.query_params.get("radius", 5000))

        from .models import Destination
        from .utils import overpass_search_nearby, bounding_box

        box = bounding_box(lat, lon, radius_m / 1000)
        own_destinations = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
            latitude__gte=box["min_lat"], latitude__lte=box["max_lat"],
            longitude__gte=box["min_lon"], longitude__lte=box["max_lon"],
        )
        own_results = [
            {"id": f"dest-{d.id}", "name": d.name, "latitude": float(d.latitude), "longitude": float(d.longitude),
             "distance": round(haversine_distance(lat, lon, d.latitude, d.longitude), 2), "category": d.category.name}
            for d in own_destinations
        ]
        osm_results = [
            {"id": f"osm-{p['osm_id']}", "name": p["name"], "latitude": p["latitude"], "longitude": p["longitude"],
             "distance": round(haversine_distance(lat, lon, p["latitude"], p["longitude"]), 2), "category": p["type"]}
            for p in overpass_search_nearby(lat, lon, radius_m)
            if p.get("latitude") is not None
        ]

        combined = sorted(own_results + osm_results, key=lambda p: p["distance"])
        return Response(combined)

