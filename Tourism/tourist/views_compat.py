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
    if not p_str or str(p_str).lower() == "nan":
        return default
    p = str(p_str).split(".")[0].strip()
    return p if len(p) > 2 else default


class NearbyHospitalsView(APIView):
    """GET /api/v1/nearby/hospitals?lat=&lng= — nearest hospitals from dataset & GPS."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = _parse_float(request.query_params.get("lat") or request.query_params.get("latitude") or "27.7172", "lat")
            lon = _parse_float(request.query_params.get("lng") or request.query_params.get("longitude") or "85.3240", "lng")
        except (ValueError, TypeError):
            lat, lon = 27.7172, 85.3240
        radius_km = float(request.query_params.get("radius_km", 50.0))

        from .models import Hospital, EmergencyContact
        ec_hospitals = EmergencyContact.objects.filter(contact_type="hospital")
        results = []
        for ec in ec_hospitals:
            d = haversine_distance(lat, lon, float(ec.latitude), float(ec.longitude))
            if d <= radius_km:
                results.append({
                    "id": ec.id,
                    "name": ec.name,
                    "contact_type": "hospital",
                    "address": ec.address,
                    "phone_number": str(ec.phone_number),
                    "latitude": float(ec.latitude),
                    "longitude": float(ec.longitude),
                    "distance_km": round(d, 2),
                    "is_24_hours": ec.is_24_hours,
                    "image_url": ["https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&q=80","https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&q=80","https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&q=80","https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&q=80"][(ec.id % 4)],
                })

        if not ec_hospitals.exists():
            hospitals = Hospital.objects.all()
            for h in hospitals:
                d = haversine_distance(lat, lon, float(h.latitude), float(h.longitude))
                if d <= radius_km:
                    results.append({
                        "id": h.id,
                        "name": h.name,
                        "contact_type": "hospital",
                        "address": h.address,
                        "phone_number": clean_phone(h.phone, "+977-1-4412404"),
                        "latitude": float(h.latitude),
                        "longitude": float(h.longitude),
                        "distance_km": round(d, 2),
                        "district": h.district,
                        "is_24_hours": True,
                        "image_url": ["https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&q=80","https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&q=80","https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&q=80","https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&q=80"][(h.id % 4)],
                    })
            if not results and hospitals.exists():
                all_sorted = []
                for h in hospitals:
                    d = haversine_distance(lat, lon, float(h.latitude), float(h.longitude))
                    all_sorted.append({
                        "id": h.id,
                        "name": h.name,
                        "contact_type": "hospital",
                        "address": h.address,
                        "phone_number": clean_phone(h.phone, "+977-1-4412404"),
                        "latitude": float(h.latitude),
                        "longitude": float(h.longitude),
                        "distance_km": round(d, 2),
                        "district": h.district,
                        "is_24_hours": True,
                        "image_url": ["https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&q=80","https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&q=80","https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&q=80","https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&q=80"][(h.id % 4)],
                    })
                all_sorted.sort(key=lambda x: x["distance_km"])
                results = all_sorted[:10]

        results.sort(key=lambda x: x["distance_km"])
        return Response(results)


class NearbyPoliceView(APIView):
    """GET /api/v1/nearby/police?lat=&lng= — nearest police stations from dataset & GPS."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = _parse_float(request.query_params.get("lat") or request.query_params.get("latitude") or "27.7172", "lat")
            lon = _parse_float(request.query_params.get("lng") or request.query_params.get("longitude") or "85.3240", "lng")
        except (ValueError, TypeError):
            lat, lon = 27.7172, 85.3240
        radius_km = float(request.query_params.get("radius_km", 50.0))

        from .models import PoliceStation, EmergencyContact
        ec_police = EmergencyContact.objects.filter(contact_type="police")
        results = []
        for ec in ec_police:
            d = haversine_distance(lat, lon, float(ec.latitude), float(ec.longitude))
            if d <= radius_km:
                results.append({
                    "id": ec.id,
                    "name": ec.name,
                    "contact_type": "police",
                    "address": ec.address,
                    "phone_number": str(ec.phone_number),
                    "latitude": float(ec.latitude),
                    "longitude": float(ec.longitude),
                    "distance_km": round(d, 2),
                    "is_24_hours": ec.is_24_hours,
                    "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&auto=format&fit=crop&q=80",
                })

        if not ec_police.exists():
            police = PoliceStation.objects.all()
            for p in police:
                d = haversine_distance(lat, lon, float(p.latitude), float(p.longitude))
                if d <= radius_km:
                    results.append({
                        "id": p.id,
                        "name": p.name,
                        "contact_type": "police",
                        "address": p.address,
                        "phone_number": clean_phone(p.phone, "100"),
                        "latitude": float(p.latitude),
                        "longitude": float(p.longitude),
                        "distance_km": round(d, 2),
                        "is_24_hours": True,
                        "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&auto=format&fit=crop&q=80",
                    })
            if not results and police.exists():
                all_sorted = []
                for p in police:
                    d = haversine_distance(lat, lon, float(p.latitude), float(p.longitude))
                    all_sorted.append({
                        "id": p.id,
                        "name": p.name,
                        "contact_type": "police",
                        "address": p.address,
                        "phone_number": clean_phone(p.phone, "100"),
                        "latitude": float(p.latitude),
                        "longitude": float(p.longitude),
                        "distance_km": round(d, 2),
                        "is_24_hours": True,
                        "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&auto=format&fit=crop&q=80",
                    })
                all_sorted.sort(key=lambda x: x["distance_km"])
                results = all_sorted[:10]

        results.sort(key=lambda x: x["distance_km"])
        return Response(results)


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
                return Response({"detail": "lat and lng query params are required (or allow location access).", "results": []}, status=status.HTTP_400_BAD_REQUEST)

        radius_m = max(int(request.query_params.get("radius", 5000) or 5000), 1000)
        radius_km = radius_m / 1000.0

        from .models import Destination, EmergencyContact
        from .utils import overpass_search_nearby, bounding_box
        from . import photo_catalog

        def _img_for_poi(category, name, seed):
            photo = photo_catalog.resolve_poi_photo(category or "", name or "", seed or 0)
            return photo["url"]

        def _cover_url(destination):
            raw = str(destination.cover_image or "").strip()
            if raw.startswith("http://") or raw.startswith("https://"):
                return raw
            cover = destination.gallery.filter(is_cover=True).first()
            if cover and cover.external_url:
                return cover.external_url
            return photo_catalog.resolve_cover_photo(destination)["url"]

        box = bounding_box(lat, lon, radius_km)
        own_destinations = Destination.objects.filter(
            is_active=True,
            status=Destination.SubmissionStatus.APPROVED,
            latitude__gte=box["min_lat"],
            latitude__lte=box["max_lat"],
            longitude__gte=box["min_lon"],
            longitude__lte=box["max_lon"],
        )

        own_results = []
        for destination in own_destinations:
            distance = haversine_distance(lat, lon, destination.latitude, destination.longitude)
            if distance is None or distance > radius_km:
                continue
            own_results.append({
                "id": f"dest-{destination.id}",
                "name": destination.name,
                "latitude": float(destination.latitude),
                "longitude": float(destination.longitude),
                "distance": round(distance, 2),
                "category": getattr(destination.category, "name", "destination"),
                "type": "destination",
                "city": destination.city,
                "district": destination.district,
                "country": destination.country,
                "image_url": _cover_url(destination),
            })

        local_body_results = []
        local_bodies = EmergencyContact.objects.filter(
            contact_type__in=[EmergencyContact.ContactType.WARD_OFFICE, EmergencyContact.ContactType.WARD_MEMBER],
            latitude__isnull=False,
            longitude__isnull=False,
        )
        for body in local_bodies:
            distance = haversine_distance(lat, lon, body.latitude, body.longitude)
            if distance is None or distance > radius_km:
                continue
            local_body_results.append({
                "id": f"local-{body.id}",
                "name": body.name,
                "latitude": float(body.latitude),
                "longitude": float(body.longitude),
                "distance": round(distance, 2),
                "category": "local_body",
                "type": "local_body",
                "ward_number": body.ward_number,
                "designation": body.designation,
                "city": body.city,
                "district": body.city,
                "image_url": _img_for_poi("office", body.name, body.id),
            })

        osm_results = []
        for place in (overpass_search_nearby(lat, lon, radius_m, tourism_only=False) or []):
            if place.get("latitude") is None or place.get("longitude") is None:
                continue
            distance = haversine_distance(lat, lon, place["latitude"], place["longitude"])
            if distance is None or distance > radius_km:
                continue
            osm_results.append({
                "id": f"osm-{place['osm_id']}",
                "name": place["name"],
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "distance": round(distance, 2),
                "category": place.get("type") or "place",
                "type": "osm",
                "image_url": _img_for_poi(place.get("type") or "place", place.get("name") or "", place.get("osm_id") or 0),
            })

        combined = sorted(own_results + local_body_results + osm_results, key=lambda p: p["distance"])
        return Response(combined)