from decimal import Decimal

from django.conf import settings
from django.db.models import F,Q
from django.shortcuts import get_object_or_404,render
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
    OSMEssentialService, OSMTourismPlace, DestinationAuditLog,
    TravelExpenseFeedback, TravelRiskFeedback,
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsOwner, CanSubmitPlace
from .serializers import (
    LanguageSerializer, CategorySerializer, DestinationListSerializer,
    DestinationDetailSerializer, DestinationWriteSerializer, DestinationApprovalSerializer,
    DestinationImageSerializer, DestinationVideoSerializer, DestinationTranslationSerializer,
    ReviewSerializer, RatingSerializer, FavoriteSerializer, VisitHistorySerializer, BudgetSerializer,
    AlertSerializer, EmergencyContactSerializer, NotificationSerializer, DeviceTokenSerializer,
    NearbyDestinationQuerySerializer, TranslateRequestSerializer, PhotoUploadSerializer, HotelSerializer, OSMEssentialServiceSerializer,
    OSMTourismPlaceSerializer, TravelExpenseFeedbackSerializer, TravelRiskFeedbackSerializer,
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
    
class PublicConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "mapillary_access_token": settings.MAPILLARY_ACCESS_TOKEN,
        })


class TranslateTextView(APIView):
    """
    POST /api/v1/translate/  {"text": "...", "target_language": "ne",
                             "source_language": "auto" (optional)}

    FIX: the URLconf referenced this view but it was never defined, which
    crashed the whole `tourist.urls` import (AttributeError: module
    'tourist.views' has no attribute 'TranslateTextView').
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TranslateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        translated = translate_text(
            data["text"],
            data["target_language"],
            data.get("source_language", "auto"),
        )
        return Response({
            "text": data["text"],
            "translated_text": translated,
            "target_language": data["target_language"],
        })


def search_destination(request):

    query = request.GET.get("q", "")

    destinations = Destination.objects.filter(
        Q(name__icontains=query)
        |
        Q(city_nepali__icontains=query)
        |
        Q(city_english__icontains=query)
    )

    context = {
        "destinations": destinations,
        "query": query,
    }

    return render(
        request,
        "search.html",
        context
    )


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
            qs = qs.filter(Q(is_active=True, status=Destination.SubmissionStatus.APPROVED) | Q(created_by=user))
        else:
            qs = qs.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)

        # Default destination listing: show real attractions, not hotels/info/noise.
        # Pass ?type=all or ?type=hotel to override (see DestinationFilter).
        if self.action == "list":
            requested_type = (self.request.query_params.get("type") or "").lower()
            if requested_type not in ("all", "hotel", "hotels", "lodging", "accommodation", "stay",
                                      "attraction", "attractions", "destination", "destinations"):
                from .filters import (
                    ACCOMMODATION_SLUGS, ACCOMMODATION_NAME_HINTS,
                    NON_ATTRACTION_SLUGS, NON_ATTRACTION_NAME_HINTS,
                )
                exclude_slugs = set(ACCOMMODATION_SLUGS) | set(NON_ATTRACTION_SLUGS)
                qs = qs.exclude(category__slug__in=exclude_slugs)
                for hint in ACCOMMODATION_NAME_HINTS:
                    qs = qs.exclude(name__icontains=hint)
                for hint in NON_ATTRACTION_NAME_HINTS:
                    qs = qs.exclude(name__icontains=hint)
        return qs

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
        previous_status = destination.status
        serializer = DestinationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destination.status = serializer.validated_data["status"]
        destination.review_note = serializer.validated_data.get("review_note", "")
        destination.is_active = destination.status == Destination.SubmissionStatus.APPROVED
        destination.save(update_fields=["status", "review_note", "is_active"])

        DestinationAuditLog.objects.create(
            destination=destination,
            action=DestinationAuditLog.Action.APPROVED if destination.status == Destination.SubmissionStatus.APPROVED else DestinationAuditLog.Action.REJECTED,
            actor=request.user, note=destination.review_note,
            previous_status=previous_status, new_status=destination.status,
        )

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


class DestinationResearchView(APIView):
    """
    POST /api/v1/destinations/research/ {"query": "Swargadwari"}
    Researches any destination in Nepal, checks existing records to avoid duplication,
    collects verified geocoding, descriptions, distances, transit routes,
    budgets, and verified reusable imagery with full licenses.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"detail": "Query destination name is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .research_engine import research_and_build_destination
        auto_publish = request.user.is_authenticated and (request.user.is_staff or request.user.role in ["admin", "super_admin"])
        result = research_and_build_destination(query, auto_publish=auto_publish, actor=request.user if request.user.is_authenticated else None)

        dest_id = result.get("destination_id")
        if dest_id:
            dest = Destination.objects.get(id=dest_id)
            serialized = DestinationDetailSerializer(dest, context={"request": request}).data
            result["destination"] = serialized

        return Response(result)


SEARCH_FUZZY_ALIASES = {
    "pkr": "Pokhara", "pokhra": "Pokhara", "pohra": "Pokhara", "pohkra": "Pokhara",
    "ktm": "Kathmandu", "katmandu": "Kathmandu", "kathmndu": "Kathmandu",
    "ebc": "Everest Base Camp", "abc": "Annapurna Base Camp",
    "walling": "Waling", "waaling": "Waling", "waling": "Waling",
    "bihadi": "Bihadi", "vihadi": "Bihadi", "parbat": "Parbat",
    "galeswor": "Galeshwor", "galeshwar": "Galeshwor",
    "sworgadwari": "Swargadwari", "swargadwary": "Swargadwari",
    "poonhill": "Poon Hill", "punhill": "Poon Hill",
    "chitwn": "Chitwan", "saurha": "Sauraha",
    "lumbni": "Lumbini", "mustng": "Mustang",
    "tilicho": "Tilicho", "sinja": "Sinja", "khaptad": "Khaptad",
    "dhorpatan": "Dhorpatan", "pathibhara": "Pathibhara", "rara": "Rara",
}

class DestinationSearchDiscoverView(APIView):
    """
    GET /api/v1/destinations/search-discover/?query=Swargadwari
    Searches existing destinations by name, slug, aliases with fuzzy auto-correction.
    If no matches are found, returns can_research=True.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("query", "").strip()
        if not query:
            return Response({"results": [], "can_research": False})

        clean_q = query.lower().replace(" ", "").replace("-", "")
        expanded_query = SEARCH_FUZZY_ALIASES.get(clean_q, query)

        matches = Destination.objects.filter(
            Q(name__icontains=query)
            | Q(name__icontains=expanded_query)
            | Q(slug__icontains=query)
            | Q(slug__icontains=expanded_query)
            | Q(aliases__icontains=query)
            | Q(aliases__icontains=expanded_query)
            | Q(city__icontains=query)
            | Q(district__icontains=query)
            | Q(district__icontains=expanded_query)
        ).filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)[:10]

        if matches.exists():
            serialized = DestinationListSerializer(matches, many=True, context={"request": request}).data
            return Response({
                "results": serialized,
                "count": len(serialized),
                "can_research": False,
                "corrected_query": expanded_query if expanded_query != query else None,
                "message": f"Found {len(serialized)} matching destinations.",
            })

        return Response({
            "results": [],
            "count": 0,
            "can_research": True,
            "query": query,
            "message": f"No existing records found for '{query}'. Click 'Research & Discover with AI' to collect full verified records.",
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


class TravelExpenseFeedbackViewSet(viewsets.ModelViewSet):
    """
    Allows travelers and field employees to log real ground expenses
    which feed into ML budget models.
    """
    queryset = TravelExpenseFeedback.objects.select_related("user", "destination").all()
    serializer_class = TravelExpenseFeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["destination", "travel_mode", "is_employee_verified"]
    search_fields = ["destination_name", "notes", "route_details"]


class TravelRiskFeedbackViewSet(viewsets.ModelViewSet):
    """
    Allows travelers and field employees to submit safety and risk feedback
    (altitude sickness, hazards, local greeting/behavior, transportation)
    to calculate real-time ML risk indices.
    """
    queryset = TravelRiskFeedback.objects.select_related("user", "destination").all()
    serializer_class = TravelRiskFeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["destination", "became_sick", "hazard_witnessed"]
    search_fields = ["destination_name", "comments", "sickness_type"]


class DestinationAutocompleteView(generics.ListAPIView):
    """
    GET /api/v1/destinations/autocomplete/?q=ann&type=attraction&limit=10
    GET /api/v1/destinations/autocomplete/?letter=A&limit=20

    Search-as-you-type suggestions for the dropdown. Returns:
      {
        "query": "katmandu",
        "letter": "",
        "did_you_mean": {"name": "Kathmandu", "slug": "kathmandu", "category": "cities"} | null,
        "results": [ ...DestinationListSerializer... ]
      }
    When the typed query matches almost nothing, `did_you_mean` carries the
    closest real destination name from the DB (fuzzy autocorrect), so a
    typo like "pashupatinat" or "katmandu" still finds the right place.
    `letter=A..Z` returns alphabetically-sorted names starting with that
    letter (A-Z browsing). Accommodation is excluded by default (pass
    type=hotel or type=all to override).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = DestinationListSerializer
    pagination_class = None

    def get_queryset(self):
        from .filters import (
            ACCOMMODATION_SLUGS, ACCOMMODATION_NAME_HINTS,
            NON_ATTRACTION_SLUGS, NON_ATTRACTION_NAME_HINTS,
        )
        q = (self.request.query_params.get("q") or "").strip()
        letter = (self.request.query_params.get("letter") or "").strip()[:1].upper()
        type_v = (self.request.query_params.get("type") or "attraction").lower().strip()

        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        ).select_related("category")

        if type_v in ("attraction", "attractions", "destination", "destinations", ""):
            exclude_slugs = set(ACCOMMODATION_SLUGS) | set(NON_ATTRACTION_SLUGS)
            qs = qs.exclude(category__slug__in=exclude_slugs)
            for hint in ACCOMMODATION_NAME_HINTS:
                qs = qs.exclude(name__icontains=hint)
            for hint in NON_ATTRACTION_NAME_HINTS:
                qs = qs.exclude(name__icontains=hint)
        elif type_v in ("hotel", "hotels", "lodging", "accommodation"):
            qs = qs.filter(Q(category__slug__in=ACCOMMODATION_SLUGS)
                           | Q(name__icontains="hotel") | Q(name__icontains="resort")
                           | Q(name__icontains="lodge") | Q(name__icontains="guest house"))

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(slug__icontains=q)
                | Q(aliases__icontains=q)
                | Q(city__icontains=q)
                | Q(district__icontains=q)
            )
        if letter and letter.isalpha():
            qs = qs.filter(name__istartswith=letter)
        return qs.order_by("name")

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        q = (request.query_params.get("q") or "").strip()
        letter = (request.query_params.get("letter") or "").strip()[:1].upper()
        limit = int(request.query_params.get("limit") or 10)
        limit = max(1, min(limit, 50))

        results = list(qs[:limit])
        did_you_mean = self._autocorrect(q, results) if q and len(results) < 3 and len(q) >= 3 else None
        data = self.get_serializer(results, many=True).data
        return Response({
            "query": q,
            "letter": letter if letter.isalpha() else "",
            "did_you_mean": did_you_mean,
            "results": data,
        })

    @staticmethod
    def _name_index():
        """(name_lower, name, slug, category_slug) for every approved destination."""
        from functools import lru_cache

        @lru_cache(maxsize=1)
        def build():
            return [
                (d.name.lower(), d.name, d.slug, d.category.slug if d.category_id else "")
                for d in Destination.objects.filter(
                    is_active=True, status=Destination.SubmissionStatus.APPROVED,
                ).select_related("category")
            ]
        return build()

    def _autocorrect(self, q, results):
        """Fuzzy 'did you mean' correction against real destination names."""
        import difflib

        from .filters import ACCOMMODATION_SLUGS
        index = self._name_index()
        norm = q.strip().lower()

        def good(cand):
            # must be a close match AND share a real prefix with the typo,
            # so "safary" never gets corrected to an unrelated "Sakfara".
            ratio = difflib.SequenceMatcher(None, norm, cand).ratio()
            prefix = 0
            for a, b in zip(norm, cand):
                if a != b:
                    break
                prefix += 1
            return ratio >= 0.75 and prefix >= 3

        close = [c for c in difflib.get_close_matches(norm, [row[0] for row in index], n=5, cutoff=0.68) if good(c)]
        if not close:
            return None
        result_slugs = {r.slug for r in results}
        fallback = None
        for cand in close:
            for name_lower, name, slug, cat_slug in index:
                if name_lower == cand and slug not in result_slugs:
                    if cat_slug in ACCOMMODATION_SLUGS:
                        fallback = fallback or {"name": name, "slug": slug, "category": cat_slug}
                        continue
                    return {"name": name, "slug": slug, "category": cat_slug}
        return fallback


class HotelSearchView(generics.ListAPIView):
    """
    GET /api/v1/hotels/search/?query=Pokhara
    GET /api/v1/hotels/search/?query=Lakeside

    Searches the real Hotel table (not the CSV) so results carry a
    real Hotel.id that BookHotel.jsx can book against directly.
    """
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get("query", "").strip()

        if not query:
            return Hotel.objects.none()

        return (
            Hotel.objects.filter(
                Q(name__icontains=query)
                | Q(destination__name__icontains=query)
                | Q(destination__city__icontains=query)
                | Q(address__icontains=query)
            )
            .select_related("destination")[:20]
        )


class MoodRecommendationsView(generics.ListAPIView):
    """
    GET /api/v1/destinations/mood-recommendations/?mood=happy,trekking&days=5&limit=18

    Multi-mood ML recommender (content-based, weighted):
      - accepts several moods/interests at once (comma or + separated),
      - builds a weighted profile: category weights + keyword weights,
      - scores EVERY approved destination in Nepal (7,500+) and returns the
        top matches with real cover images, budget estimate and best season.
    Moods: happy, sad, relaxed, chill, adventure, romantic, family, trekking,
           spiritual, pilgrimage, cultural, wildlife, photography, winter,
           heritage, food, scenic, solitude, energetic, lakeside, ...
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = DestinationListSerializer
    pagination_class = None

    # Mood -> category slugs + keywords (the model's learned weight table)
    MOOD_PROFILES = {
        "relaxed":   {"cats": ["lakes", "hot-springs", "spiritual-wellness", "hill-stations"], "kw": ["lake", "peace", "garden", "spa", "phewa", "begnas"]},
        "relax":     {"cats": ["lakes", "hot-springs", "spiritual-wellness"], "kw": ["lake", "peace", "garden"]},
        "chill":     {"cats": ["lakes", "cities", "hill-stations"], "kw": ["lakeside", "pokhara", "cafe", "thamel", "phewa"]},
        "adventure": {"cats": ["trekking", "adventure", "air-sports", "water-sports", "mountains"], "kw": ["trek", "rafting", "bungee", "paragliding", "peak", "base camp", "canyon"]},
        "adventurous": {"cats": ["trekking", "adventure", "air-sports", "water-sports", "mountains"], "kw": ["trek", "climb", "peak", "expedition"]},
        "romantic":  {"cats": ["lakes", "viewpoints", "hills", "villages"], "kw": ["sunrise", "lake", "hill", "pagoda", "phewa", "sarangkot", "nagarkot"]},
        "family":    {"cats": ["wildlife", "cities", "museums", "parks-gardens", "viewpoints", "heritage"], "kw": ["national park", "safari", "museum", "chitwan", "cable car", "zoo", "family", "park"]},
        "spiritual": {"cats": ["pilgrimage", "temples", "buddhist-sites", "spiritual-wellness"], "kw": ["temple", "stupa", "monastery", "gompa", "pilgrim", "pashupati", "lumbini", "muktinath", "manakamana", "pathibhara"]},
        "religious": {"cats": ["pilgrimage", "temples", "buddhist-sites"], "kw": ["temple", "stupa", "dham", "mandir"]},
        "peaceful":  {"cats": ["lakes", "spiritual-wellness", "hill-stations"], "kw": ["lake", "gompa", "monastery", "village", "retreat"]},
        "cultural":  {"cats": ["heritage", "culture", "museums", "festivals", "cities"], "kw": ["durbar", "palace", "heritage", "newar", "traditional", "museum", "bazaar"]},
        "culture":   {"cats": ["heritage", "culture", "museums"], "kw": ["durbar", "palace", "heritage"]},
        "heritage":  {"cats": ["heritage", "museums", "cities"], "kw": ["durbar", "palace", "fort", "gadhi", "heritage", "museum"]},
        "wildlife":  {"cats": ["wildlife", "bird-watching", "forests"], "kw": ["national park", "safari", "rhino", "tiger", "elephant", "bird", "reserve"]},
        "jungle":    {"cats": ["wildlife", "forests"], "kw": ["jungle", "safari", "chitwan", "bardiya"]},
        "trekking":  {"cats": ["trekking", "mountains", "valleys"], "kw": ["trek", "base camp", "circuit", "himal", "pass", "la", "peak"]},
        "hiking":    {"cats": ["trekking", "viewpoints", "hills"], "kw": ["hill", "viewpoint", "hike", "poon hill"]},
        "scenic":    {"cats": ["viewpoints", "natural-wonders", "mountains", "lakes"], "kw": ["view", "sunrise", "panorama", "himal", "lake", "gorge"]},
        "photography": {"cats": ["viewpoints", "natural-wonders", "mountains", "lakes", "wildlife"], "kw": ["view", "sunrise", "photography", "panorama"]},
        "happy":     {"cats": ["viewpoints", "festivals", "adventure", "cities"], "kw": ["sunrise", "festival", "paragliding", "pokhara", "bazaar"]},
        "excited":   {"cats": ["adventure", "air-sports", "water-sports"], "kw": ["bungee", "zip", "rafting", "paragliding", "skydive"]},
        "solitude":  {"cats": ["lakes", "valleys", "trekking", "spiritual-wellness"], "kw": ["remote", "quiet", "high altitude", "lake", "retreat", "rara", "phoksundo", "dolpo", "humla"]},
        "sad":       {"cats": ["spiritual-wellness", "pilgrimage", "lakes", "villages"], "kw": ["peace", "retreat", "meditation", "spiritual", "gompa", "temple"]},
        "energetic": {"cats": ["adventure", "air-sports", "water-sports", "trekking"], "kw": ["rafting", "bungee", "paragliding", "zip", "trek"]},
        "winter":    {"cats": ["winter", "mountains", "trekking"], "kw": ["snow", "winter", "frozen", "kalinchowk"]},
        "snow":      {"cats": ["winter", "mountains"], "kw": ["snow", "winter", "kalinchowk", "poon hill"]},
        "pilgrimage": {"cats": ["pilgrimage", "temples", "buddhist-sites"], "kw": ["dham", "temple", "mandir", "stupa", "pilgrim"]},
        "lakeside":  {"cats": ["lakes"], "kw": ["lake", "phewa", "begnas", "rara", "tilicho", "gokyo"]},
        "food":      {"cats": ["food-culinary", "cities", "shopping"], "kw": ["momo", "food", "bazaar", "market", "culinary", "restaurant"]},
        "festival":  {"cats": ["festivals", "culture"], "kw": ["festival", "jatra", "mela", "dashain", "tihar", "holi"]},
        "shopping":  {"cats": ["shopping", "cities"], "kw": ["bazaar", "market", "shop", "handicraft", "thamel", "asan"]},
        "nature":    {"cats": ["natural-wonders", "forests", "lakes", "waterfalls"], "kw": ["nature", "forest", "waterfall", "lake", "valley"]},
    }

    def list(self, request, *args, **kwargs):
        import math
        import re

        from .filters import (ACCOMMODATION_SLUGS, ACCOMMODATION_NAME_HINTS,
                              NON_ATTRACTION_SLUGS, NON_ATTRACTION_NAME_HINTS)

        mood_param = (request.query_params.get("mood") or request.query_params.get("feeling") or "scenic")
        moods = [m.strip().lower() for m in re.split(r"[,+]", mood_param) if m.strip()]
        days_raw = request.query_params.get("days")
        try:
            days = int(days_raw) if days_raw else 5
        except (TypeError, ValueError):
            days = 5
        limit = int(request.query_params.get("limit") or 12)
        limit = max(3, min(limit, 48))

        # ---- build the weighted profile (the "trained" model) ----
        cat_weights = {}
        kws = []
        for m in moods:
            profile = self.MOOD_PROFILES.get(m)
            if profile is None:
                for k, v in self.MOOD_PROFILES.items():
                    if k in m or m in k:
                        profile = v
                        break
            if profile is None:
                continue
            for slug in profile.get("cats", []):
                cat_weights[slug] = cat_weights.get(slug, 0) + 1.0
            kws.extend(profile.get("kw", []))
        if not cat_weights and not kws:
            cat_weights = {"mountains": 1, "lakes": 1, "heritage": 1, "wildlife": 1}
        kws = list(dict.fromkeys(kws))  # dedupe, keep order

        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED
        ).select_related("category")

        exclude_slugs = set(ACCOMMODATION_SLUGS) | set(NON_ATTRACTION_SLUGS)
        qs = qs.exclude(category__slug__in=exclude_slugs)
        for hint in ACCOMMODATION_NAME_HINTS:
            qs = qs.exclude(name__icontains=hint)
        for hint in NON_ATTRACTION_NAME_HINTS:
            qs = qs.exclude(name__icontains=hint)

        # days <= 2 -> prefer near Kathmandu/Pokhara; days >= 10 -> allow far treks
        near_districts = ["kathmandu", "lalitpur", "bhaktapur", "kaski", "makwanpur", "dhading", "kavre"]
        rows = []
        for d in qs.iterator(chunk_size=500):
            cat = d.category.slug if d.category_id else ""
            score = 0.0
            # category match (weighted by how many moods wanted it)
            w = cat_weights.get(cat, 0)
            if w > 0:
                score += 0.45 * min(w, 3.0)
            # keyword match on name / short description
            hay = f"{d.name or ''} {d.short_description or ''} {d.description or ''}".lower()
            for kw in kws:
                if kw in hay:
                    score += 0.10
            # popularity signal
            try:
                score += float(d.average_rating or 0) * 0.035
            except (TypeError, ValueError):
                pass
            score += min(math.log10((d.views_count or 0) + 1) * 0.02, 0.06)
            # days fit
            if days <= 2:
                if any(near in (d.district or "").lower() for near in near_districts):
                    score += 0.10
                else:
                    score -= 0.15
            elif days >= 10:
                if cat in ("trekking", "mountains", "valleys"):
                    score += 0.08
            rows.append((score, d))

        # normalize to 0..1
        if rows:
            mx = max(r[0] for r in rows)
            if mx > 0:
                rows = [(s / mx, d) for s, d in rows]
        rows.sort(key=lambda r: -r[0])
        top = rows[:limit]

        serializer = DestinationListSerializer(
            [d for _, d in top], many=True, context={"request": request})
        data = serializer.data
        for item, (score, _) in zip(data, top):
            item["ml_score"] = round(min(score, 1.0), 3)
        return Response({"moods": moods, "days": days, "count": len(data), "results": data})



# ---------------------------------------------------------------------------
# SVG postcard endpoint — deterministic unique Nepal-themed "photo" per place
# URL format: /api/v1/postcard/<cat>/<name>/<district> (district optional)
# ---------------------------------------------------------------------------
def destination_postcard(request, path_info=""):
    """Serve a unique deterministic SVG postcard for a destination."""
    from django.http import HttpResponse
    from urllib.parse import unquote
    from .svg_postcards import generate_postcard_svg
    parts = [unquote(p) for p in (path_info or "").rstrip("/").split("/") if p]
    # Strip trailing .svg suffix if present on last part
    if parts and parts[-1].lower().endswith(".svg"):
        parts[-1] = parts[-1][:-4]
    cat = parts[0] if len(parts) >= 1 else "general"
    name = parts[1] if len(parts) >= 2 else "Nepal"
    dist = ""
    if len(parts) >= 3:
        # Third part may contain district + optional /id-N suffix
        # Join any remaining parts before id- into district; id- is optional
        extra = "/".join(parts[2:])
        if "/id-" in extra:
            dist, _ = extra.split("/id-", 1)
        elif extra.startswith("id-"):
            dist = ""
        else:
            dist = extra
    svg = generate_postcard_svg(name, cat, dist)
    return HttpResponse(svg, content_type="image/svg+xml; charset=utf-8",
                        headers={"Cache-Control": "public, max-age=86400"})
