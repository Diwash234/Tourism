from decimal import Decimal

from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, permissions, status, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import DestinationFilter, AlertFilter, EmergencyContactFilter, BudgetFilter
from .models import (
    Language, Category, Destination, DestinationImage, DestinationVideo,
    DestinationTranslation, Review, Rating, Favorite, VisitHistory, Budget,
    Alert, EmergencyContact, Notification, DeviceToken, Hotel,
    OSMEssentialService, OSMTourismPlace,

)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsOwner, CanSubmitPlace
from .serializers import (
    LanguageSerializer, CategorySerializer, DestinationListSerializer,
    DestinationDetailSerializer, DestinationWriteSerializer, DestinationApprovalSerializer,
    DestinationImageSerializer, DestinationVideoSerializer, DestinationTranslationSerializer,
    ReviewSerializer, RatingSerializer, FavoriteSerializer, VisitHistorySerializer, BudgetSerializer,
    AlertSerializer, EmergencyContactSerializer, NotificationSerializer, DeviceTokenSerializer,
    NearbyDestinationQuerySerializer, TranslateRequestSerializer, PhotoUploadSerializer, HotelSerializer, OSMEssentialServiceSerializer,
    OSMTourismPlaceSerializer,
)
from .utils import (
    haversine_distance, bounding_box, translate_text, notify_user,
    get_destination_photos, register_photo_view, get_current_weather, overpass_search_nearby,
    find_nearby_places, get_disaster_helplines,
)


class UserLocationContextMixin:
    """Injects the requesting user's lat/lon into serializer context for distance annotations."""

    def get_user_coords(self):
        lat = self.request.query_params.get("latitude") or self.request.query_params.get("lat")
        lon = self.request.query_params.get("longitude") or self.request.query_params.get("lon")
        if lat is None or lon is None:
            user = self.request.user
            if user.is_authenticated and user.latitude is not None and user.longitude is not None:
                lat, lon = user.latitude, user.longitude
        return lat, lon

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lat, lon = self.get_user_coords()
        context["user_lat"] = lat
        context["user_lon"] = lon
        return context


class UserScopedQuerysetMixin:
    """
    Returns an empty queryset during schema generation (drf-spectacular
    calls get_queryset() with an AnonymousUser), avoiding type errors on
    querysets filtered by request.user.
    """

    def get_queryset_for_user(self, base_queryset):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return base_queryset.none()
        return base_queryset


class LanguageViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = []
    pagination_class = None


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "description"]
    ordering_fields = ["name"]
    lookup_field = "slug"


class QueryParamAliasMixin:
    """
    Accepts a few common alternate query param names so frontends built
    against a slightly different API contract don't silently get
    unfiltered/wrongly-paginated results: `q` as an alias for `search`,
    `limit` as an alias for `page_size`.
    """

    def filter_queryset(self, queryset):
        params = self.request.query_params.copy()
        if "q" in params and not params.get("search"):
            params["search"] = params["q"]
        if "limit" in params and not params.get("page_size"):
            params["page_size"] = params["limit"]
        self.request._request.GET = params
        return super().filter_queryset(queryset)


class DestinationViewSet(QueryParamAliasMixin, UserLocationContextMixin, viewsets.ModelViewSet):
    queryset = Destination.objects.select_related("category", "created_by")
    permission_classes = [CanSubmitPlace]
    filterset_class = DestinationFilter
    search_fields = ["name", "description", "city", "country"]
    ordering_fields = ["average_rating", "entry_fee", "created_at", "name", "views_count"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return DestinationListSerializer
        if self.action in ("create", "update", "partial_update"):
            return DestinationWriteSerializer
        if self.action == "approve":
            return DestinationApprovalSerializer
        return DestinationDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        if user.is_authenticated and user.is_staff:
            return qs  # staff see everything, including pending submissions
        if user.is_authenticated:
            # Public approved places + this user's own submissions (any status)
            from django.db.models import Q
            return qs.filter(Q(is_active=True, status=Destination.SubmissionStatus.APPROVED) | Q(created_by=user))
        return qs.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Destination.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
        instance.refresh_from_db(fields=["views_count"])
        if request.user.is_authenticated:
            VisitHistory.objects.create(user=request.user, destination=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter("latitude", float, required=True),
            OpenApiParameter("longitude", float, required=True),
            OpenApiParameter("radius_km", float, required=False),
        ]
    )
    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def nearby(self, request):
        """
        Returns approved destinations within `radius_km` of the given
        coordinates, nearest first, each annotated with `distance_km` — the
        straight-line distance the user needs to travel to reach it.
        """
        query_serializer = NearbyDestinationQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        lat = query_serializer.validated_data["latitude"]
        lon = query_serializer.validated_data["longitude"]
        radius_km = query_serializer.validated_data["radius_km"]

        box = bounding_box(lat, lon, radius_km)
        candidates = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
            latitude__gte=box["min_lat"], latitude__lte=box["max_lat"],
            longitude__gte=box["min_lon"], longitude__lte=box["max_lon"],
        )

        results = []
        for dest in candidates:
            distance = haversine_distance(lat, lon, dest.latitude, dest.longitude)
            if distance <= radius_km:
                results.append((distance, dest))
        results.sort(key=lambda pair: pair[0])
        destinations = [dest for _, dest in results]

        page = self.paginate_queryset(destinations)
        serializer = DestinationListSerializer(
            page or destinations, many=True, context={"request": request, "user_lat": lat, "user_lon": lon}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def translate(self, request, slug=None):
        """Auto-translates this destination's description/alerts into the requested language."""
        destination = self.get_object()
        target_lang = request.data.get("language_code") or request.data.get("target_language")
        if not target_lang:
            return Response({"detail": "language_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        language = get_object_or_404(Language, code=target_lang)
        translation, _ = DestinationTranslation.objects.get_or_create(
            destination=destination, language=language,
            defaults={"name": destination.name, "description": destination.description,
                      "short_description": destination.short_description},
        )
        translation.name = translate_text(destination.name, target_lang)
        translation.description = translate_text(destination.description, target_lang)
        translation.short_description = translate_text(destination.short_description, target_lang)
        translation.is_auto_generated = True
        translation.save()
        return Response(DestinationTranslationSerializer(translation).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, slug=None):
        """Admin-only: approve or reject a tourist-submitted place."""
        destination = self.get_object()
        serializer = DestinationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destination.status = serializer.validated_data["status"]
        destination.review_note = serializer.validated_data.get("review_note", "")
        destination.is_active = destination.status == Destination.SubmissionStatus.APPROVED
        destination.save(update_fields=["status", "review_note", "is_active"])

        if destination.created_by:
            notify_user(
                destination.created_by,
                title=f"Your submission was {destination.status}",
                message=f'"{destination.name}" was {destination.status}. {destination.review_note}'.strip(),
                channel="email",
            )
        return Response(DestinationDetailSerializer(destination, context={"request": request}).data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_submissions(self, request):
        """Lists the requesting user's own submitted places, including pending/rejected ones."""
        qs = Destination.objects.filter(created_by=request.user).select_related("category")
        page = self.paginate_queryset(qs)
        serializer = DestinationListSerializer(page or qs, many=True, context=self.get_serializer_context())
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def photos(self, request, slug=None):
        """
        GET  — the destination's photo gallery: local uploads (community +
               admin, most-viewed/promoted first). If none exist yet, one
               Unsplash/Wikimedia fallback image is fetched ONCE and cached
               as a real gallery entry (source=unsplash/wikimedia) — see
               tourist/utils.py::ensure_cover_photo() — so this never
               re-hits the external API on subsequent calls.
        POST — any authenticated user ("local people") can contribute a
               photo here. It's tagged as a community upload and starts
               un-promoted; if it becomes popular (crosses
               PHOTO_PROMOTION_IMPRESSION_THRESHOLD views), it's
               automatically promoted to the official cover photo — see
               tourist/utils.py::maybe_promote_photo().
        """
        destination = self.get_object()

        if request.method == "POST":
            serializer = PhotoUploadSerializer(data={**request.data, "destination": destination.id}, context={"request": request})
            serializer.is_valid(raise_exception=True)
            photo = serializer.save()
            return Response(DestinationImageSerializer(photo, context={"request": request}).data, status=status.HTTP_201_CREATED)

        photos = get_destination_photos(destination)
        for photo in photos:
            register_photo_view(photo)

        return Response({
            "photos": DestinationImageSerializer(photos, many=True, context={"request": request}).data,
        })

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def weather(self, request, slug=None):
        """Current weather at this destination's coordinates, via OpenWeatherMap."""
        destination = self.get_object()
        result = get_current_weather(destination.latitude, destination.longitude)
        if result is None:
            return Response(
                {"detail": "Weather data is currently unavailable (check OPENWEATHER_API_KEY)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(result)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def essentials(self, request, slug=None):
        """
        GET /api/v1/destinations/{slug}/essentials/
        One combined "everything you need for this place" bundle: hotels
        (from your own Hotel table, sourced via import_hotels or the
        dataset), nearby restaurants/shops (live from Foursquare/Google
        Places if configured), current weather, and — if there's an active
        disaster alert covering this area — the nearest police/hospital/
        ward contacts to call right now (see utils.py::get_disaster_helplines).
        Every section degrades independently: a missing API key or down
        service empties that one section rather than failing the request.
        """
        destination = self.get_object()

        hotels = HotelSerializer(destination.hotels.all(), many=True).data
        restaurants = find_nearby_places(destination.latitude, destination.longitude, "restaurant")
        shops = find_nearby_places(destination.latitude, destination.longitude, "shop")
        weather = get_current_weather(destination.latitude, destination.longitude)
        disaster_info = get_disaster_helplines(destination)

        return Response({
            "hotels": hotels,
            "restaurants": restaurants,
            "shops": shops,
            "weather": weather,
            "active_alert": disaster_info["active_alert"],
            "emergency_helplines": disaster_info["helplines"],
        })


class DestinationImageViewSet(viewsets.ModelViewSet):
    queryset = DestinationImage.objects.all()
    serializer_class = DestinationImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["destination"]


class HotelViewSet(viewsets.ModelViewSet):
    """
    Accommodation options with booking-availability status. Public read;
    admin write. Populate via `python manage.py import_hotels` from your
    dataset, or by syncing from Google Places/Foursquare.
    """

    queryset = Hotel.objects.select_related("destination")
    serializer_class = HotelSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["destination", "booking_status", "source"]
    ordering_fields = ["price_per_night", "rating"]
    search_fields = ["name", "address"]


class DestinationVideoViewSet(viewsets.ModelViewSet):
    queryset = DestinationVideo.objects.all()
    serializer_class = DestinationVideoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["destination"]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("user", "destination")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_fields = ["destination", "user"]
    ordering_fields = ["created_at"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.select_related("user", "destination")
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_fields = ["destination", "user"]

    def perform_create(self, serializer):
        rating = serializer.save(user=self.request.user)
        rating.destination.recalculate_rating()

    def perform_update(self, serializer):
        rating = serializer.save()
        rating.destination.recalculate_rating()

    def perform_destroy(self, instance):
        destination = instance.destination
        instance.delete()
        destination.recalculate_rating()


class FavoriteViewSet(UserScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Favorite.objects.none()
        return Favorite.objects.filter(user=self.request.user).select_related("destination")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VisitHistoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = VisitHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VisitHistory.objects.none()
        return VisitHistory.objects.filter(user=self.request.user).select_related("destination")


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = BudgetFilter
    ordering_fields = ["date", "amount"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Budget.objects.none()
        return Budget.objects.filter(user=self.request.user).select_related("destination")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AlertViewSet(UserLocationContextMixin, viewsets.ModelViewSet):
    queryset = Alert.objects.filter(is_active=True)
    serializer_class = AlertSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = AlertFilter
    search_fields = ["title", "description", "city"]
    ordering_fields = ["created_at", "severity"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def nearby(self, request):
        """Returns active alerts within `radius_km` of the given coordinates."""
        query_serializer = NearbyDestinationQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        lat = query_serializer.validated_data["latitude"]
        lon = query_serializer.validated_data["longitude"]
        radius_km = query_serializer.validated_data["radius_km"]

        results = []
        for alert in self.get_queryset().exclude(latitude__isnull=True):
            distance = haversine_distance(lat, lon, alert.latitude, alert.longitude)
            if distance <= radius_km:
                results.append((distance, alert))
        results.sort(key=lambda pair: pair[0])
        alerts = [a for _, a in results]
        serializer = self.get_serializer(alerts, many=True, context={"request": request, "user_lat": lat, "user_lon": lon})
        return Response(serializer.data)


class EmergencyContactViewSet(UserLocationContextMixin, viewsets.ModelViewSet):
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = EmergencyContactFilter
    search_fields = ["name", "city", "address"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def nearest(self, request):
        """
        Returns the single nearest emergency contact of each requested type
        (police, hospital, tourism_office, fire_station, ...) to the given coordinates.
        """
        query_serializer = NearbyDestinationQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        lat = query_serializer.validated_data["latitude"]
        lon = query_serializer.validated_data["longitude"]
        radius_km = query_serializer.validated_data["radius_km"]

        contact_type = request.query_params.get("contact_type")
        qs = self.get_queryset()
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
        serializer = self.get_serializer(contacts, many=True, context={"request": request, "user_lat": lat, "user_lon": lon})
        return Response(serializer.data)


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["channel", "is_read"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post", "put"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"message": "All notifications marked as read."})


class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DeviceToken.objects.none()
        return DeviceToken.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TranslateTextView(APIView):
    """Generic text translation endpoint (used for alerts/emergency info/UI strings)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = TranslateRequestSerializer

    def post(self, request):
        serializer = TranslateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        translated = translate_text(
            serializer.validated_data["text"],
            serializer.validated_data["target_language"],
            serializer.validated_data.get("source_language", "auto"),
        )
        return Response({"translated_text": translated})


class OSMNearbyPlacesView(APIView):
    """
    GET /api/v1/places/osm-nearby/?latitude=&longitude=&radius_m=
    Raw OpenStreetMap (Overpass API) tourism/amenity points near a
    location — useful for discovering places not yet in your own
    Destination table. Free, no API key required.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = NearbyDestinationQuerySerializer

    def get(self, request):
        try:
            latitude = float(request.query_params["latitude"])
            longitude = float(request.query_params["longitude"])
        except (KeyError, ValueError):
            return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)
        radius_m = int(request.query_params.get("radius_m", 2000))

        places = overpass_search_nearby(latitude, longitude, radius_m)
        return Response({"count": len(places), "results": places})
    
class OSMTourismPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns tourism places imported from OpenStreetMap.
    """

    queryset = OSMTourismPlace.objects.all()
    serializer_class = OSMTourismPlaceSerializer
    permission_classes = [permissions.AllowAny]

    filterset_fields = ["category"]
    search_fields = ["name", "address"]


class OSMEssentialServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns emergency and essential services imported from OpenStreetMap.
    """

    queryset = OSMEssentialService.objects.all()
    serializer_class = OSMEssentialServiceSerializer
    permission_classes = [permissions.AllowAny]

    filterset_fields = ["category"]
    search_fields = ["name", "address"]