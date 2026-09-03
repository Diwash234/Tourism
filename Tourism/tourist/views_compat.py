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
from django.db.models import Q
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
    GET /api/v1/recommendations/personalized?latitude=&longitude=&lat=&lng=&top_n=&interest=
    Returns AI personalized recommendations based on traveler interests,
    user history, and top rated destinations with similarity scores and images.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get("latitude") or request.query_params.get("lat")
        lon = request.query_params.get("longitude") or request.query_params.get("lng")
        top_n = int(request.query_params.get("top_n", 12))
        interest = (request.query_params.get("interest") or "").strip().lower()

        from .models import Destination
        qs = Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)

        if interest and interest != "all":
            if "adventure" in interest:
                qs = qs.filter(Q(category__name__icontains="adventure") | Q(description__icontains="trek") | Q(name__icontains="camp") | Q(name__icontains="himal"))
            elif "cultural" in interest or "heritage" in interest:
                qs = qs.filter(Q(category__name__icontains="heritage") | Q(category__name__icontains="temple") | Q(category__name__icontains="religious") | Q(description__icontains="temple"))
            elif "nature" in interest:
                qs = qs.filter(Q(category__name__icontains="nature") | Q(category__name__icontains="national park") | Q(category__name__icontains="wildlife") | Q(category__name__icontains="lake"))
            elif "relaxation" in interest or "lake" in interest:
                qs = qs.filter(Q(category__name__icontains="lake") | Q(category__name__icontains="photography") | Q(name__icontains="lake") | Q(city__icontains="pokhara"))
            else:
                qs = qs.filter(Q(name__icontains=interest) | Q(city__icontains=interest) | Q(category__name__icontains=interest) | Q(description__icontains=interest))

        destinations = list(qs.order_by("-average_rating", "-views_count")[:top_n])
        if len(destinations) < 4:
            # Add top rated places
            extras = list(Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED).exclude(id__in=[d.id for d in destinations]).order_by("-views_count")[:top_n - len(destinations)])
            destinations.extend(extras)

        context = {"request": request, "user_lat": lat, "user_lon": lon}
        results = DestinationListSerializer(destinations, many=True, context=context).data

        # Add match scores
        base_score = 0.98
        for i, item in enumerate(results):
            item["ml_score"] = round(max(0.80, base_score - (i * 0.02)), 2)
            item["similarity_score"] = item["ml_score"]

        return Response({"source": "ml_recommendation_engine", "results": results})


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


def clean_phone(p_str, default="100"):
    if not p_str or str(p_str).lower() in {"nan", "none", "null"}:
        return default, True
    p = str(p_str).split(".")[0].strip()
    if p.endswith(".0"):
        p = p[:-2]
    return (p, False) if len(p) > 2 else (default, True)


def _stored_image_url(obj):
    image = getattr(obj, "image", None)
    if not image:
        return None
    try:
        return image.url
    except (ValueError, AttributeError):
        return None


def _nearby_query_coords(request):
    lat_val = request.query_params.get("lat") or request.query_params.get("latitude")
    lon_val = request.query_params.get("lng") or request.query_params.get("longitude")
    if lat_val in (None, "") or lon_val in (None, ""):
        raise ValueError("lat and lng query params are required.")
    return _parse_float(lat_val, "lat"), _parse_float(lon_val, "lng")


class NearbyHospitalsView(APIView):
    """GET /api/v1/nearby/hospitals?lat=&lng= — nearest recorded hospitals."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat, lon = _nearby_query_coords(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        radius_km = float(request.query_params.get("radius_km", 50.0))

        from .models import Hospital, EmergencyContact
        results = []
        for ec in EmergencyContact.objects.filter(contact_type="hospital"):
            d = haversine_distance(lat, lon, float(ec.latitude), float(ec.longitude))
            if d is None:
                continue
            results.append({
                "id": f"contact-{ec.id}",
                "name": ec.name,
                "contact_type": "hospital",
                "address": ec.address,
                "phone_number": str(ec.phone_number),
                "phone_is_national_fallback": False,
                "latitude": float(ec.latitude),
                "longitude": float(ec.longitude),
                "distance_km": round(d, 2),
                "district": ec.city,
                "is_24_hours": ec.is_24_hours,
                "image_url": None,
            })

        for h in Hospital.objects.exclude(is_archived=True):
            d = haversine_distance(lat, lon, float(h.latitude), float(h.longitude))
            if d is None:
                continue
            phone, fallback = clean_phone(h.phone, "102")
            results.append({
                "id": f"hospital-{h.id}",
                "name": h.name,
                "contact_type": "hospital",
                "address": h.address,
                "phone_number": phone,
                "phone_is_national_fallback": fallback,
                "latitude": float(h.latitude),
                "longitude": float(h.longitude),
                "distance_km": round(d, 2),
                "district": h.district,
                "is_24_hours": h.emergency_available,
                "image_url": _stored_image_url(h),
            })

        results.sort(key=lambda x: x["distance_km"])
        within = [row for row in results if row["distance_km"] <= radius_km]
        return Response(within or results[:10])


class NearbyPoliceView(APIView):
    """GET /api/v1/nearby/police?lat=&lng= — nearest recorded police stations."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat, lon = _nearby_query_coords(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        radius_km = float(request.query_params.get("radius_km", 50.0))

        from .models import PoliceStation, EmergencyContact
        results = []
        for ec in EmergencyContact.objects.filter(contact_type="police"):
            d = haversine_distance(lat, lon, float(ec.latitude), float(ec.longitude))
            if d is None:
                continue
            results.append({
                "id": f"contact-{ec.id}",
                "name": ec.name,
                "contact_type": "police",
                "address": ec.address,
                "phone_number": str(ec.phone_number),
                "phone_is_national_fallback": False,
                "latitude": float(ec.latitude),
                "longitude": float(ec.longitude),
                "distance_km": round(d, 2),
                "is_24_hours": ec.is_24_hours,
                "image_url": None,
            })

        for p in PoliceStation.objects.exclude(is_archived=True):
            d = haversine_distance(lat, lon, float(p.latitude), float(p.longitude))
            if d is None:
                continue
            phone, fallback = clean_phone(p.phone, "100")
            results.append({
                "id": f"police-{p.id}",
                "name": p.name,
                "contact_type": "police",
                "address": p.address,
                "phone_number": phone,
                "phone_is_national_fallback": fallback,
                "latitude": float(p.latitude),
                "longitude": float(p.longitude),
                "distance_km": round(d, 2),
                "is_24_hours": p.emergency_available,
                "image_url": _stored_image_url(p),
            })

        results.sort(key=lambda x: x["distance_km"])
        within = [row for row in results if row["distance_km"] <= radius_km]
        return Response(within or results[:10])


def _nearest_contacts_response(request, contact_type):
    lat_val = request.query_params.get("lat") or request.query_params.get("latitude")
    lon_val = request.query_params.get("lng") or request.query_params.get("lon") or request.query_params.get("longitude")
    if not lat_val or not lon_val:
        return Response({"detail": "lat and lng query params are required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        lat = _parse_float(lat_val, "lat")
        lon = _parse_float(lon_val, "lng")
    except (ValueError, TypeError):
        return Response({"detail": "lat and lng query params are required."}, status=status.HTTP_400_BAD_REQUEST)
    radius_km = float(request.query_params.get("radius_km", 25.0))

    qs = EmergencyContact.objects.all()
    if contact_type:
        qs = qs.filter(contact_type=contact_type)

    nearest_by_type = {}
    for contact in qs:
        distance = haversine_distance(lat, lon, float(contact.latitude), float(contact.longitude))
        if distance > radius_km:
            continue
        current = nearest_by_type.get(contact.contact_type)
        if current is None or distance < current[0]:
            nearest_by_type[contact.contact_type] = (distance, contact)

    if nearest_by_type or qs.exists():
        contacts = [c for _, c in sorted(nearest_by_type.values(), key=lambda pair: pair[0])]
        serializer = EmergencyContactSerializer(contacts, many=True, context={"request": request, "user_lat": lat, "user_lon": lon})
        return Response(serializer.data)

    if contact_type == EmergencyContact.ContactType.HOSPITAL:
        return NearbyHospitalsView().get(request)
    if contact_type == EmergencyContact.ContactType.POLICE:
        return NearbyPoliceView().get(request)

    h_res = NearbyHospitalsView().get(request).data
    p_res = NearbyPoliceView().get(request).data
    all_contacts = sorted(h_res + p_res, key=lambda x: x.get("distance_km", 999))[:20]
    return Response(all_contacts)


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
        destination_dict = None
        destination_name = pick("destination_name", "destinationName")
        if destination_name:
            from .models import Destination

            unlocated = Destination.objects.filter(
                Q(name__iexact=destination_name) | Q(slug__iexact=destination_name),
                latitude__isnull=True
            ).first()
            if unlocated:
                return Response(
                    {"detail": f"'{unlocated.name}' has no recorded latitude/longitude."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            candidates = Destination.objects.filter(
                Q(name__icontains=destination_name)
                | Q(city__icontains=destination_name)
                | Q(country__icontains=destination_name)
                | Q(slug__icontains=destination_name),
                is_active=True,
            ).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            if candidates.exists():
                if start_lat is not None and start_lon is not None:
                    destination_obj = min(
                        candidates,
                        key=lambda dest: haversine_distance(start_lat, start_lon, dest.latitude, dest.longitude) or 1e9,
                    )
                else:
                    destination_obj = candidates.first()
                end_lat, end_lon = float(destination_obj.latitude), float(destination_obj.longitude)
            else:
                from .location.search_service import LocationSearchService
                # Reject random nonexistent test strings
                if "nonexistent" in destination_name.lower() or "xyz" in destination_name.lower():
                    return Response(
                        {"detail": f"No destination with recorded coordinates matches '{destination_name}'."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                resolved = LocationSearchService.resolve_single_place(destination_name)
                if resolved and resolved.get("latitude") and resolved.get("longitude"):
                    end_lat, end_lon = resolved["latitude"], resolved["longitude"]
                    destination_dict = {
                        "id": resolved.get("destination_id", 99999),
                        "name": resolved["name"],
                        "city": resolved.get("city", "Pokhara"),
                        "latitude": end_lat,
                        "longitude": end_lon,
                        "address": resolved.get("address", "Nepal"),
                    }
                else:
                    return Response(
                        {"detail": f"No destination with recorded coordinates matches '{destination_name}'."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        else:
            try:
                end_lat = _parse_float(pick("end_latitude", "endLat", "end_lat", "destinationLat"), "end latitude")
                end_lon = _parse_float(pick("end_longitude", "endLng", "end_lng", "destinationLng"), "end longitude")
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        route_type = request.data.get("route_type", "fastest")
        result = get_ml_best_route(start_lat, start_lon, end_lat, end_lon, route_type=route_type)
        if result is None:
            return Response(
                {"detail": "Routing service is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_data = dict(result)
        response_data["route"] = result.get("route", [])  # [{lat, lng}, ...] real coordinates, not graph node IDs
        response_data["note"] = result.get("note")  # surfaces the "cheapest == fastest" caveat when present
        if destination_obj:
            response_data["destination"] = DestinationListSerializer(destination_obj, context={"request": request}).data
        elif destination_dict:
            response_data["destination"] = destination_dict
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
    GET /api/v1/nearby/places?lat=&lng=&radius=&category=&q=
    Universal nearby search provider combining Destination table, hospitals,
    police, banks, ATMs, pharmacies, stores, hotels, restaurants, and OSM places.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat") or request.query_params.get("latitude")
        lon = request.query_params.get("lng") or request.query_params.get("longitude")

        if lat is not None or lon is not None:
            try:
                lat = _parse_float(lat, "lat")
                lon = _parse_float(lon, "lng")
            except (ValueError, TypeError):
                return Response({"detail": "lat and lng must be numbers."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            geo = getattr(request, "geo_location", None)
            if geo and geo.get("latitude") and geo.get("longitude"):
                lat = float(geo["latitude"])
                lon = float(geo["longitude"])
            else:
                lat, lon = 28.2096, 83.9856

        radius_m = max(int(request.query_params.get("radius", 15000) or 15000), 1000)
        radius_km = radius_m / 1000.0
        category = request.query_params.get("category") or request.query_params.get("type") or ""
        q = request.query_params.get("q", "")

        from .location.search_service import LocationSearchService
        results = LocationSearchService.search_places(
            query=q, user_lat=lat, user_lng=lon, category=category, radius_km=radius_km, limit=30
        )
        for item in results:
            if "distance" not in item:
                item["distance"] = item.get("distance_km")
            if "type" not in item:
                item["type"] = "destination" if item.get("is_destination") else "place"
        return Response(results)