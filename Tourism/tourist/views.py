from decimal import Decimal

from django.conf import settings
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404,render
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, permissions, status, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import DestinationFilter, AlertFilter, EmergencyContactFilter, BudgetFilter
from .models import (
    Language, Category, Destination, DestinationImage, DestinationVideo,
    DestinationTranslation, Review, Rating, Favorite, VisitHistory, Budget,
    Alert, EmergencyContact, Notification, NotificationPreference, DeviceToken, Hotel,
    OSMEssentialService, OSMTourismPlace, DestinationAuditLog,
    TravelExpenseFeedback, TravelRiskFeedback, InfrastructureSubmission, InfrastructureMedia,
    CurrentHazard, RiskIncident, RiskObservation, RecommendationEvent, RiskNewsReport,
    SiteSetting, ManagedPage, ContentSection, ManagedNavigationItem, CMSContentTranslation, DestinationFeatureProfile,
    Restaurant, DestinationTransitRoute, TravelPlan, TravelPlanStop,
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsOwner, CanSubmitPlace, HasCapability, HasCapabilityOrReadOnly
from .serializers import (
    LanguageSerializer, CategorySerializer, DestinationListSerializer,
    DestinationDetailSerializer, DestinationWriteSerializer, DestinationApprovalSerializer,
    DestinationImageSerializer, DestinationVideoSerializer, DestinationTranslationSerializer,
    ReviewSerializer, RatingSerializer, FavoriteSerializer, VisitHistorySerializer, BudgetSerializer,
    AlertSerializer, EmergencyContactSerializer, NotificationSerializer, NotificationPreferenceSerializer, DeviceTokenSerializer,
    NearbyDestinationQuerySerializer, TranslateRequestSerializer, PhotoUploadSerializer, HotelSerializer, OSMEssentialServiceSerializer,
    OSMTourismPlaceSerializer, TravelExpenseFeedbackSerializer, TravelRiskFeedbackSerializer,
    InfrastructureSubmissionSerializer, InfrastructureMediaSerializer, RiskNewsReportSerializer, DestinationFeatureProfileSerializer,
    RiskIncidentAdminSerializer, CurrentHazardAdminSerializer, RiskObservationAdminSerializer,
    RestaurantSerializer, DestinationTransitRouteSerializer, TravelPlanSerializer, TravelPlanStopSerializer,
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


class RiskIncidentAdminViewSet(viewsets.ModelViewSet):
    queryset = RiskIncident.objects.select_related("destination").all()
    serializer_class = RiskIncidentAdminSerializer
    permission_classes = [HasCapability]
    capability_module = "safety"
    filterset_fields = ["destination", "hazard_type", "severity", "source_type", "verified"]
    search_fields = ["destination__name", "title", "description", "affected_area", "source_name"]

    def perform_destroy(self, instance):
        instance.is_archived=True;instance.archived_at=timezone.now();instance.save(update_fields=["is_archived","archived_at","updated_at"])

class CurrentHazardAdminViewSet(viewsets.ModelViewSet):
    queryset = CurrentHazard.objects.select_related("destination").all()
    serializer_class = CurrentHazardAdminSerializer
    permission_classes = [HasCapability]
    capability_module = "safety"
    filterset_fields = ["destination", "hazard_type", "severity", "source_type", "is_active", "verified"]
    search_fields = ["destination__name", "title", "description", "source_name", "station_name"]

    def perform_destroy(self, instance):
        instance.is_active=False;instance.expires_at=instance.expires_at or timezone.now();instance.save(update_fields=["is_active","expires_at","updated_at"])

class RiskObservationAdminViewSet(viewsets.ModelViewSet):
    queryset = RiskObservation.objects.select_related("destination").all()
    serializer_class = RiskObservationAdminSerializer
    permission_classes = [HasCapability]
    capability_module = "safety"
    filterset_fields = ["destination", "observation_type", "trend", "source_type", "verified"]
    search_fields = ["destination__name", "station_name", "source_name"]

    def perform_destroy(self, instance):
        instance.is_archived=True;instance.archived_at=timezone.now();instance.save(update_fields=["is_archived","archived_at","updated_at"])

class DestinationTranslationAdminViewSet(viewsets.ModelViewSet):
    queryset = DestinationTranslation.objects.select_related("destination", "language").all()
    serializer_class = DestinationTranslationSerializer
    permission_classes = [HasCapability]
    capability_module = "content"
    filterset_fields = ["destination", "language", "is_auto_generated"]
    search_fields = ["destination__name", "name", "description"]


class DestinationFeatureProfileViewSet(viewsets.ModelViewSet):
    queryset = DestinationFeatureProfile.objects.select_related("destination").all()
    serializer_class = DestinationFeatureProfileSerializer
    permission_classes = [HasCapability]
    capability_module = "destinations"
    filterset_fields = ["destination", "difficulty", "budget_level", "is_verified"]
    search_fields = ["destination__name", "source_type"]


class LanguageViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = []
    pagination_class = None


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "destinations"
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
        import re
        now = timezone.now()
        ManagedPage.objects.filter(status="scheduled", scheduled_publish_at__lte=now).update(
            status="published", published_at=now, scheduled_publish_at=None)
        ContentSection.objects.filter(status="scheduled", scheduled_publish_at__lte=now).update(
            status="published", published_at=now, scheduled_publish_at=None)
        language = request.query_params.get("lang", "en")
        if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", language):
            language = "en"
        translations = {(row.target_resource, row.object_id): row.content for row in
            CMSContentTranslation.objects.filter(language_code=language)} if language != "en" else {}
        pages = ManagedPage.objects.filter(is_enabled=True, status="published").prefetch_related("sections")
        page_rows = []
        for page in pages:
            page_translation = translations.get(("pages", page.id), {})
            sections = []
            for section in page.sections.filter(is_visible=True, status="published"):
                translated = translations.get(("sections", section.id), {})
                sections.append({"id": section.id, "key": section.key,
                    "title": translated.get("title", section.title), "subtitle": translated.get("subtitle", section.subtitle),
                    "body": translated.get("body", section.body), "image_url": section.image_url,
                    "cta_text": translated.get("cta_text", section.cta_text), "cta_url": section.cta_url,
                    "icon": section.icon, "section_type": section.section_type,
                    "layout_variant": section.layout_variant, "config": section.config,
                    "display_order": section.display_order})
            page_rows.append({"id": page.id, "key": page.key, "route": page.route,
                "title": page_translation.get("title", page.title),
                "seo_title": page.seo_title, "og_image_url": page.og_image_url,
                "search_visible": page.search_visible,
                "meta_description": page_translation.get("meta_description", page.meta_description), "sections": sections})
        navigation = []
        for item in ManagedNavigationItem.objects.filter(is_active=True):
            translated = translations.get(("navigation", item.id), {})
            navigation.append({"id": item.id, "location": item.location,
                "label": translated.get("label", item.label), "route": item.route, "icon": item.icon,
                "parent_id": item.parent_id, "allowed_roles": item.allowed_roles, "display_order": item.display_order})
        from .notices import active_notices_qs, serialize_notice
        notices = [serialize_notice(notice) for notice in active_notices_qs(now)[:20]]
        return Response({"mapillary_access_token": settings.MAPILLARY_ACCESS_TOKEN, "language": language,
            "settings": {item.key: item.value for item in SiteSetting.objects.filter(is_public=True)},
            "pages": page_rows, "navigation": navigation, "notices": notices})


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
    queryset = Destination.objects.select_related("category", "created_by").prefetch_related("gallery")
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

    def perform_destroy(self, instance):
        previous=instance.status
        instance.status=Destination.SubmissionStatus.ARCHIVED;instance.is_active=False
        instance.save(update_fields=["status","is_active","updated_at"])
        DestinationAuditLog.objects.create(destination=instance,actor=self.request.user,
            action=DestinationAuditLog.Action.EDITED,note="Destination archived through retention-safe deletion",
            previous_status=previous,new_status=instance.status)

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

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def videos(self, request, slug=None):
        destination = self.get_object()
        if request.method == "POST":
            if not request.user.is_authenticated:
                return Response({"detail": "Login required to submit a video."}, status=status.HTTP_401_UNAUTHORIZED)
            payload = {key: request.data.get(key) for key in request.data}
            payload["destination"] = destination.id
            serializer = DestinationVideoSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
            video = serializer.save()
            return Response(DestinationVideoSerializer(video, context={"request": request}).data, status=status.HTTP_201_CREATED)
        queryset = destination.videos.filter(verification_status="approved")
        if request.user.is_authenticated:
            queryset = destination.videos.filter(
                Q(verification_status="approved") | Q(uploaded_by=request.user)
            ).exclude(verification_status="rejected")
        return Response({
            "videos": DestinationVideoSerializer(queryset, many=True, context={"request": request}).data,
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

        hotels = HotelSerializer(destination.hotels.filter(is_active=True).select_related("destination").prefetch_related("destination__gallery"), many=True, context={"request": request}).data
        database_restaurants = RestaurantSerializer(destination.restaurants.filter(status="published"), many=True).data
        external_restaurants = find_nearby_places(destination.latitude, destination.longitude, "restaurant")
        restaurants = database_restaurants or external_restaurants
        shops = find_nearby_places(destination.latitude, destination.longitude, "shop")
        weather = get_current_weather(destination.latitude, destination.longitude)
        disaster_info = get_disaster_helplines(destination)

        return Response({
            "hotels": hotels,
            "restaurants": restaurants,
            "restaurant_source": "database" if database_restaurants else "external_live" if external_restaurants else "unavailable",
            "external_restaurants": external_restaurants if database_restaurants else [],
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
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "images"
    filterset_fields = ["destination"]


class HotelViewSet(viewsets.ModelViewSet):
    """
    Accommodation options with booking-availability status. Public read;
    admin write. Populate via `python manage.py import_hotels` from your
    dataset, or by syncing from Google Places/Foursquare.
    """

    serializer_class = HotelSerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "hotels"
    filterset_fields = ["destination", "booking_status", "source"]
    ordering_fields = ["price_per_night", "rating"]
    search_fields = ["name", "address"]

    def get_queryset(self):
        queryset=Hotel.objects.select_related("destination").prefetch_related("destination__gallery")
        user=self.request.user
        if self.request.method in permissions.SAFE_METHODS and not (user.is_authenticated and (user.is_superuser or user.role in {"admin","super_admin","tourism_admin"})):
            queryset=queryset.filter(is_active=True)
        return queryset

    def perform_destroy(self, instance):
        instance.is_active=False;instance.archived_at=timezone.now();instance.booking_status=Hotel.BookingStatus.UNAVAILABLE
        instance.save(update_fields=["is_active","archived_at","booking_status","updated_at"])


class RestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = RestaurantSerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "restaurants"
    filterset_fields = ["destination", "price_range", "vegetarian_friendly", "status", "is_verified"]
    search_fields = ["name", "cuisine_types", "address"]

    def get_queryset(self):
        queryset = Restaurant.objects.select_related("destination")
        user = self.request.user
        if self.request.method in permissions.SAFE_METHODS and not (user.is_authenticated and (user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"})):
            queryset = queryset.filter(status="published")
        return queryset

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user, status="pending", is_verified=False)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.status="archived";instance.updated_by=self.request.user;instance.save(update_fields=["status","updated_by","updated_at"])


class TransitRouteViewSet(viewsets.ModelViewSet):
    serializer_class = DestinationTransitRouteSerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "transportation"
    filterset_fields = ["destination", "transport_mode", "is_active", "is_verified"]
    search_fields = ["origin", "transport_mode", "operator_name", "key_stops"]

    def get_queryset(self):
        queryset = DestinationTransitRoute.objects.select_related("destination")
        if self.request.method in permissions.SAFE_METHODS:
            queryset = queryset.filter(is_active=True)
        return queryset

    def perform_create(self, serializer): serializer.save(updated_by=self.request.user, is_verified=False)
    def perform_update(self, serializer): serializer.save(updated_by=self.request.user)
    def perform_destroy(self, instance):
        instance.is_active=False;instance.updated_by=self.request.user;instance.save(update_fields=["is_active","updated_by","updated_at"])


class TravelPlanViewSet(viewsets.ModelViewSet):
    serializer_class = TravelPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "generation_source"]
    search_fields = ["title", "notes"]

    def _allows(self, action="view"):
        user=self.request.user
        if user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}: return True
        profile=getattr(user,"capability_profile",None)
        return bool(profile and profile.allows("travel_plans", action))

    def _can_manage(self): return self._allows("view")

    def get_queryset(self):
        queryset=TravelPlan.objects.select_related("user").prefetch_related("stops__destination")
        return queryset if self._can_manage() else queryset.filter(user=self.request.user).exclude(status="archived")

    def perform_create(self, serializer): serializer.save(user=self.request.user, status="draft")

    def update(self, request, *args, **kwargs):
        instance=self.get_object()
        if instance.user_id != request.user.id and not self._allows("change"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Missing travel_plans.change capability")
        return super().update(request,*args,**kwargs)

    def destroy(self, request, *args, **kwargs):
        instance=self.get_object()
        if instance.user_id != request.user.id and not self._allows("delete"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Missing travel_plans.delete capability")
        return super().destroy(request,*args,**kwargs)

    def perform_destroy(self, instance):
        instance.status="archived";instance.save(update_fields=["status","updated_at"])


class TravelPlanStopViewSet(viewsets.ModelViewSet):
    serializer_class = TravelPlanStopSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self): return TravelPlanStop.objects.filter(plan__user=self.request.user).select_related("destination", "transit_route")

    def perform_create(self, serializer):
        plan=serializer.validated_data["plan"]
        if plan.user_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only edit your own travel plans")
        serializer.save()


class DestinationVideoViewSet(viewsets.ModelViewSet):
    queryset = DestinationVideo.objects.all()
    serializer_class = DestinationVideoSerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "images"
    filterset_fields = ["destination"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.role in {"admin", "super_admin", "tourism_admin"}):
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(verification_status="approved") | Q(uploaded_by=user)).exclude(verification_status="rejected")
        return queryset.filter(verification_status="approved")


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("user", "destination")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_fields = ["destination", "user"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(Q(moderation_status="approved") | Q(user=self.request.user)).exclude(moderation_status="archived")
        return queryset.filter(moderation_status="approved")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, moderation_status="pending")

    def perform_update(self, serializer):
        serializer.save(moderation_status="pending", is_flagged=False, moderation_note="", moderated_by=None, moderated_at=None)

    def perform_destroy(self, instance):
        instance.moderation_status = "archived"
        instance.moderation_note = "Withdrawn by review owner"
        instance.moderated_at = timezone.now()
        instance.save(update_fields=["moderation_status", "moderation_note", "moderated_at", "updated_at"])


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
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "safety"
    filterset_class = AlertFilter
    search_fields = ["title", "description", "city"]
    ordering_fields = ["created_at", "severity"]

    def perform_destroy(self, instance):
        instance.is_active=False
        if not instance.ends_at: instance.ends_at=timezone.now()
        instance.save(update_fields=["is_active","ends_at","updated_at"])

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
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "safety"
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
    filterset_fields = ["channel", "category", "is_read", "delivery_status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post", "put"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post", "put"])
    def mark_unread(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = False; notification.read_at = None
        notification.save(update_fields=["is_read", "read_at"])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True, read_at=timezone.now())
        return Response({"message": "All notifications marked as read."})

    @action(detail=False, methods=["post"])
    def mark_all_unread(self, request):
        self.get_queryset().update(is_read=False, read_at=None)
        return Response({"message": "All notifications marked as unread."})


class NotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return Response(NotificationPreferenceSerializer(preference).data)

    def patch(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True); serializer.save()
        return Response(serializer.data)


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

    queryset = OSMEssentialService.objects.exclude(is_archived=True)
    serializer_class = OSMEssentialServiceSerializer
    permission_classes = [permissions.AllowAny]

    filterset_fields = ["category"]
    search_fields = ["name", "address"]


class RiskNewsReportViewSet(viewsets.ModelViewSet):
    serializer_class = RiskNewsReportSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["destination", "hazard_type", "verification_status"]
    search_fields = ["title", "summary", "affected_area", "source_name"]

    def get_queryset(self):
        qs = RiskNewsReport.objects.select_related("destination")
        user = self.request.user
        if not user.is_authenticated or not (user.is_staff or user.role in {"admin", "super_admin", "tourism_admin", "content_moderator"}):
            qs = qs.filter(verification_status="verified")
        return qs


class RecommendationEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.data.get("consented", False):
            return Response({"detail": "Explicit interaction-data consent is required."}, status=status.HTTP_400_BAD_REQUEST)
        event_type = request.data.get("event_type")
        if event_type not in dict(RecommendationEvent.EventType.choices):
            return Response({"detail": "Invalid event_type."}, status=status.HTTP_400_BAD_REQUEST)
        destination = None
        if request.data.get("destination"):
            destination = Destination.objects.filter(pk=request.data["destination"]).first()
            if not destination:
                return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)
        event = RecommendationEvent.objects.create(
            user=request.user, destination=destination, event_type=event_type,
            session_key=request.session.session_key or "", query=request.data.get("query", "")[:300],
            score=request.data.get("score"), context=request.data.get("context", {}), consented=True,
        )
        return Response({"id": event.id, "created_at": event.created_at}, status=status.HTTP_201_CREATED)


class InfrastructureSubmissionViewSet(viewsets.ModelViewSet):
    """Traveler service/place submissions; publication always requires admin review."""

    serializer_class = InfrastructureSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["place_type", "status", "district", "province"]
    search_fields = ["name", "address", "city", "municipality", "district"]

    def get_queryset(self):
        qs = InfrastructureSubmission.objects.select_related("submitted_by", "destination", "reviewed_by")
        user = self.request.user
        if user.is_staff or user.role in {"admin", "super_admin", "tourism_admin", "content_moderator", "district_manager"}:
            return qs
        return qs.filter(submitted_by=user)

    @action(detail=True, methods=["post"], url_path="media")
    def upload_media(self, request, pk=None):
        submission = self.get_object()
        files = request.FILES.getlist("files") or ([request.FILES["file"]] if request.FILES.get("file") else [])
        if not files:
            return Response({"detail": "At least one media file is required."}, status=status.HTTP_400_BAD_REQUEST)
        if len(files) > 12:
            return Response({"detail": "A maximum of 12 files can be uploaded at once."}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        for uploaded in files:
            content_type = (uploaded.content_type or "").lower()
            media_type = "video" if content_type.startswith("video/") else "image"
            media = InfrastructureMedia.objects.create(
                submission=submission, media_type=media_type, file=uploaded,
                caption=request.data.get("caption", ""), is_primary=not submission.media.exists(),
            )
            created.append(media)
        return Response(
            InfrastructureMediaSerializer(created, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ScopedFieldFeedbackMixin:
    capability_module = None

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}:
            return queryset
        profile = getattr(user, "capability_profile", None)
        if profile and profile.allows(self.capability_module, "view"):
            districts = list(profile.managed_districts or [])
            if user.managed_district and user.managed_district not in districts:
                districts.append(user.managed_district)
            return queryset.filter(destination__district__in=districts) if districts else queryset
        return queryset.filter(user=user)

    def _can_change(self, instance):
        user = self.request.user
        if instance.user_id == user.id or user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}:
            return True
        profile = getattr(user, "capability_profile", None)
        return bool(profile and profile.allows(self.capability_module, "change"))

    def update(self, request, *args, **kwargs):
        if not self._can_change(self.get_object()):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Missing change capability for this field record")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._can_change(self.get_object()):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Missing change capability for this field record")
        return super().destroy(request, *args, **kwargs)


class TravelExpenseFeedbackViewSet(ScopedFieldFeedbackMixin, viewsets.ModelViewSet):
    """Private expense submissions scoped to owner or assigned budget staff."""
    queryset = TravelExpenseFeedback.objects.select_related("user", "destination").all()
    serializer_class = TravelExpenseFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    capability_module = "budget"
    filterset_fields = ["destination", "travel_mode", "is_employee_verified"]
    search_fields = ["destination_name", "notes", "route_details"]


class TravelRiskFeedbackViewSet(ScopedFieldFeedbackMixin, viewsets.ModelViewSet):
    """Private safety submissions scoped to owner or assigned safety staff."""
    queryset = TravelRiskFeedback.objects.select_related("user", "destination").all()
    serializer_class = TravelRiskFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    capability_module = "safety"
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
            Hotel.objects.filter(is_active=True).filter(
                Q(name__icontains=query)
                | Q(destination__name__icontains=query)
                | Q(destination__city__icontains=query)
                | Q(address__icontains=query)
            )
            .select_related("destination").prefetch_related("destination__gallery")[:20]
        )


class RouteMetricsView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            values = [float(request.data[key]) for key in ["start_latitude", "start_longitude", "end_latitude", "end_longitude"]]
        except (KeyError, TypeError, ValueError):
            return Response({"detail": "Valid start/end latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)
        from .routing_service import route_metrics
        return Response(route_metrics(*values))


class NearbyEmergencyServicesView(APIView):
    """Nearest Nepal emergency services for raw GPS coordinates."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            latitude = float(request.query_params["latitude"])
            longitude = float(request.query_params["longitude"])
            radius_km = max(1, min(float(request.query_params.get("radius_km", 50)), 300))
            limit = max(1, min(int(request.query_params.get("limit", 8)), 25))
        except (KeyError, TypeError, ValueError):
            return Response(
                {"detail": "Valid latitude and longitude query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .emergency_service import build_emergency_directory
        return Response(build_emergency_directory(latitude, longitude, radius_km=radius_km, limit=limit))


class DestinationEmergencyServicesView(APIView):
    """Nearest services plus destination risk for any approved Nepal place."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, destination_ref):
        from .emergency_service import build_emergency_directory, resolve_destination
        destination = resolve_destination(destination_ref)
        if destination is None:
            return Response({"detail": "Approved destination not found."}, status=status.HTTP_404_NOT_FOUND)

        latitude, longitude = destination.latitude, destination.longitude
        coordinate_source = "destination"
        coordinate_note = "Exact stored destination coordinates"
        if latitude is None or longitude is None:
            # A small portion of imported destinations lack point geometry.
            # Use a disclosed city/district centroid so emergency lookup still
            # works country-wide; never pretend the proxy is the exact place.
            from django.db.models import Avg
            nearby_locations = Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED,
            ).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            if destination.city:
                aggregate = nearby_locations.filter(city__iexact=destination.city).aggregate(
                    latitude=Avg("latitude"), longitude=Avg("longitude")
                )
                coordinate_source = "city_centroid_proxy"
                coordinate_note = f"Approximate centroid for {destination.city}"
            else:
                aggregate = {"latitude": None, "longitude": None}
            if aggregate["latitude"] is None and destination.district:
                aggregate = nearby_locations.filter(district__iexact=destination.district).aggregate(
                    latitude=Avg("latitude"), longitude=Avg("longitude")
                )
                coordinate_source = "district_centroid_proxy"
                coordinate_note = f"Approximate centroid for {destination.district} district"
            latitude, longitude = aggregate["latitude"], aggregate["longitude"]
            if latitude is None or longitude is None:
                return Response(
                    {"detail": "No destination or district coordinates are available for distance calculation."},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        try:
            radius_km = max(1, min(float(request.query_params.get("radius_km", 50)), 300))
            limit = max(1, min(int(request.query_params.get("limit", 8)), 25))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid radius or limit."}, status=status.HTTP_400_BAD_REQUEST)

        payload = build_emergency_directory(
            latitude, longitude, destination=destination,
            radius_km=radius_km, limit=limit,
        )
        payload["location"]["source"] = coordinate_source
        payload["location"]["coordinate_note"] = coordinate_note
        from .risk_service import build_destination_risk
        payload["risk"] = build_destination_risk(destination)
        return Response(payload)


class FeaturedGalleryView(APIView):
    """Named Nepal collections requested by the visual archive UI."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        requested = [
            ("annapurna-base-camp", "Annapurna Base Camp"),
            ("bandipur-heritage-hill-station", "Bandipur Heritage"),
            ("bardiya-national-park", "Bardiya National Park"),
            ("bhaktapur-durbar-square", "Bhaktapur Durbar Square"),
            ("chitwan-national-park", "Chitwan National Park"),
            ("dolpo-shey-gompa", "Dolpo Shey Gompa"),
            ("everest-base-camp", "Everest Base Camp"),
            ("gosaikunda", "Gosaikunda"),
            ("ilam-tea-gardens-kanyam", "Ilam Tea Gardens"),
            ("janakpurdham-janaki-mandir", "Janakpurdham"),
            ("kathmandu-durbar-square", "Kathmandu Durbar Square"),
            ("koshi-tappu-wildlife-reserve", "Koshi Tappu"),
            ("lumbini-sacred-garden-maya-devi-temple", "Lumbini"),
            ("manaslu-circuit-trek", "Manaslu Circuit"),
            ("upper-mustang-lo-manthang", "Upper Mustang"),
            ("nagarkot-himalayan-sunrise-viewpoint", "Nagarkot"),
            ("patan-durbar-square", "Patan Durbar Square"),
            ("pokhara", "Pokhara"),
            ("rara-lake", "Rara Lake"),
            ("tilicho-lake", "Tilicho Lake"),
        ]
        destinations, seen = [], set()
        for slug, name in requested:
            destination = Destination.objects.filter(slug=slug, is_active=True, status="approved").first()
            if destination is None:
                destination = Destination.objects.filter(name__icontains=name, is_active=True, status="approved").order_by("-average_rating", "-views_count").first()
            if destination and destination.id not in seen:
                seen.add(destination.id); destinations.append(destination)
        return Response({
            "count": len(destinations),
            "results": DestinationListSerializer(destinations, many=True, context={"request": request}).data,
        })


class DistrictGalleryView(APIView):
    """Up to five destination-linked media items per represented Nepal district."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .serializers import is_destination_specific_image
        from .image_server import image_server_url
        canonical_districts = [
            "Bhojpur","Dhankuta","Ilam","Jhapa","Khotang","Morang","Okhaldhunga","Panchthar","Sankhuwasabha","Solukhumbu","Sunsari","Taplejung","Terhathum","Udayapur",
            "Bara","Dhanusha","Mahottari","Parsa","Rautahat","Saptari","Sarlahi","Siraha",
            "Bhaktapur","Chitwan","Dhading","Dolakha","Kathmandu","Kavrepalanchok","Lalitpur","Makwanpur","Nuwakot","Ramechhap","Rasuwa","Sindhuli","Sindhupalchok",
            "Baglung","Gorkha","Kaski","Lamjung","Manang","Mustang","Myagdi","Nawalpur","Parbat","Syangja","Tanahun",
            "Arghakhanchi","Banke","Bardiya","Dang","Gulmi","Kapilvastu","Parasi","Palpa","Pyuthan","Rolpa","Rukum East","Rupandehi",
            "Dailekh","Dolpa","Humla","Jajarkot","Jumla","Kalikot","Mugu","Rukum West","Salyan","Surkhet",
            "Achham","Baitadi","Bajhang","Bajura","Dadeldhura","Darchula","Doti","Kailali","Kanchanpur",
        ]
        lookup = {name.lower(): name for name in canonical_districts}
        lookup.update({"kavre": "Kavrepalanchok", "tanahu": "Tanahun", "nawalparasi east": "Nawalpur", "nawalparasi west": "Parasi", "east rukum": "Rukum East", "west rukum": "Rukum West", "bardiya": "Bardiya", "kapilbastu": "Kapilvastu"})
        groups = {district: [] for district in canonical_districts}
        photos = DestinationImage.objects.select_related("destination").exclude(verification_status="rejected").order_by("destination__district", "-is_cover", "id")
        for photo in photos.iterator(chunk_size=500):
            destination = photo.destination
            raw_district = (destination.district or "").strip().lower().replace(" district", "")
            district = lookup.get(raw_district)
            if not district or len(groups[district]) >= 5:
                continue
            if not is_destination_specific_image(destination, photo):
                continue
            if photo.image_path:
                url = image_server_url(photo.image_path)
            elif photo.external_url:
                url = photo.external_url
            elif photo.image:
                url = request.build_absolute_uri(photo.image.url)
            else:
                continue
            groups.setdefault(district, []).append({
                "id": photo.id, "url": url, "caption": photo.caption or destination.name,
                "destination_id": destination.id, "destination_name": destination.name,
                "destination_slug": destination.slug, "province": destination.province,
                "category_name": destination.category.name if destination.category else "landscape",
                "source": photo.source, "source_url": photo.source_url,
                "photographer": photo.photographer, "license": photo.license_type,
                "verification_status": photo.verification_status,
            })
        return Response({
            "district_count": len(groups),
            "image_count": sum(len(items) for items in groups.values()),
            "districts": [{"district": district, "images": images} for district, images in sorted(groups.items())],
        })


class DestinationRiskAssessmentView(APIView):
    """Risk evidence for any approved Nepal destination, resolved by slug/id/name."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, destination_ref):
        lookup = Q(slug__iexact=destination_ref) | Q(name__iexact=destination_ref)
        if str(destination_ref).isdigit():
            lookup |= Q(pk=int(destination_ref))
        destination = Destination.objects.filter(
            lookup, is_active=True, status=Destination.SubmissionStatus.APPROVED
        ).select_related("risk_analysis").first()
        if destination is None:
            destination = Destination.objects.filter(
                Q(name__icontains=destination_ref) | Q(city__icontains=destination_ref) |
                Q(district__icontains=destination_ref),
                is_active=True, status=Destination.SubmissionStatus.APPROVED,
            ).select_related("risk_analysis").first()
        if destination is None:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        from .risk_service import build_destination_risk
        return Response(build_destination_risk(destination))


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
            days = max(1, min(int(days_raw or 5), 30))
        except (TypeError, ValueError):
            days = 5
        limit = max(3, min(int(request.query_params.get("limit") or 12), 36))
        budget = (request.query_params.get("budget") or "any").lower()
        difficulty = (request.query_params.get("difficulty") or "any").lower()
        season = (request.query_params.get("season") or "any").lower()
        travel_style = (request.query_params.get("travel_style") or "any").lower()
        province = (request.query_params.get("province") or "").strip().lower()

        # Build the weighted profile while preserving the existing mood model.
        cat_weights, kws = {}, []
        for mood in moods:
            profile = self.MOOD_PROFILES.get(mood)
            if profile is None:
                profile = next((v for key, v in self.MOOD_PROFILES.items() if key in mood or mood in key), None)
            if not profile:
                continue
            for slug in profile.get("cats", []):
                cat_weights[slug] = cat_weights.get(slug, 0) + 1.0
            kws.extend(profile.get("kw", []))
        if not cat_weights and not kws:
            cat_weights = {"mountains": 1, "lakes": 1, "heritage": 1, "wildlife": 1}
        kws = list(dict.fromkeys(kws))

        # The live database is the source of truth: newly approved admin/user
        # destinations automatically participate without retraining a CSV model.
        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED
        ).select_related("category", "risk_analysis").prefetch_related("transit_routes").annotate(
            hospital_total=Count("hospitals", distinct=True),
            police_total=Count("police_stations", distinct=True),
            hotel_total=Count("hotels", distinct=True),
        )

        exclude_slugs = set(ACCOMMODATION_SLUGS) | set(NON_ATTRACTION_SLUGS)
        qs = qs.exclude(category__slug__in=exclude_slugs)
        for hint in ACCOMMODATION_NAME_HINTS:
            qs = qs.exclude(name__icontains=hint)
        for hint in NON_ATTRACTION_NAME_HINTS:
            qs = qs.exclude(name__icontains=hint)
        if province:
            qs = qs.filter(province__icontains=province)

        # Existing user behaviour adds a small category-affinity signal; it
        # never replaces the current content model or explicit form choices.
        affinity = {}
        if request.user.is_authenticated:
            favorite_categories = Favorite.objects.filter(user=request.user).values_list(
                "destination__category__slug", flat=True
            )
            for slug in favorite_categories:
                if slug:
                    affinity[slug] = affinity.get(slug, 0) + 1

        near_districts = ["kathmandu", "lalitpur", "bhaktapur", "kaski", "makwanpur", "dhading", "kavre"]
        # Current sourced warnings are distinct from historical/model risk and
        # receive stronger, recency-appropriate ranking influence.
        from django.utils import timezone
        active_hazards = CurrentHazard.objects.filter(is_active=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
        ).values("destination_id", "severity", "verified", "source_type", "title")
        severity_order = {"low": 1, "moderate": 2, "high": 3, "critical": 4}
        current_warning_by_destination = {}
        for hazard in active_hazards:
            previous = current_warning_by_destination.get(hazard["destination_id"])
            if previous is None or severity_order.get(hazard["severity"], 0) > severity_order.get(previous["severity"], 0):
                current_warning_by_destination[hazard["destination_id"]] = hazard

        high_altitude_cats = {"mountains", "trekking", "winter", "valleys"}
        easy_cats = {"cities", "heritage", "museums", "parks-gardens", "shopping", "food-culinary"}
        rows = []
        for destination in qs.iterator(chunk_size=500):
            cat = destination.category.slug if destination.category_id else ""
            hay = f"{destination.name or ''} {destination.short_description or ''} {destination.description or ''} {destination.city or ''} {destination.district or ''}".lower()
            score, reasons, breakdown = 0.05, [], {}

            category_score = 0.45 * min(cat_weights.get(cat, 0), 3.0)
            if category_score:
                score += category_score
                reasons.append(f"Matches your {', '.join(moods[:2])} interests")
            keyword_hits = [kw for kw in kws if kw in hay]
            keyword_score = min(len(keyword_hits) * 0.09, 0.36)
            score += keyword_score
            if keyword_hits:
                reasons.append("Relevant experiences: " + ", ".join(keyword_hits[:3]))
            breakdown["interests"] = round(category_score + keyword_score, 3)

            duration_score = 0.0
            recommended_days = destination.recommended_days or 2
            if abs(recommended_days - days) <= 1:
                duration_score = 0.18
                reasons.append(f"Fits a {days}-day trip")
            elif days <= 2 and any(x in (destination.district or "").lower() for x in near_districts):
                duration_score = 0.10
            elif days >= 10 and cat in high_altitude_cats:
                duration_score = 0.10
            score += duration_score
            breakdown["duration"] = duration_score

            inferred_difficulty = "hard" if cat in high_altitude_cats and recommended_days >= 4 else ("easy" if cat in easy_cats else "moderate")
            difficulty_score = 0.0
            if difficulty != "any":
                difficulty_score = 0.16 if difficulty == inferred_difficulty else -0.08
                if difficulty == inferred_difficulty:
                    reasons.append(f"{inferred_difficulty.title()} difficulty match")
            score += difficulty_score
            breakdown["difficulty"] = difficulty_score

            estimated_daily = float(destination.entry_fee or 0) + (30 if cat in easy_cats else 50 if cat not in high_altitude_cats else 75)
            inferred_budget = "low" if estimated_daily <= 40 else "medium" if estimated_daily <= 80 else "high"
            budget_score = 0.0
            if budget != "any":
                budget_score = 0.14 if budget == inferred_budget else -0.06
                if budget == inferred_budget:
                    reasons.append(f"Fits a {budget} budget")
            score += budget_score
            breakdown["budget"] = budget_score

            season_score = 0.0
            best_season = (destination.best_time_to_visit or "").lower()
            if season != "any" and season in best_season:
                season_score = 0.12
                reasons.append(f"Recommended in {season.title()}")
            score += season_score
            breakdown["season"] = season_score

            if travel_style == "family" and cat in {"wildlife", "cities", "museums", "parks-gardens", "heritage"}:
                score += 0.14
                reasons.append("Family-friendly experience")
            elif travel_style == "solo" and cat in {"cities", "trekking", "spiritual-wellness"}:
                score += 0.10
                reasons.append("Suitable for solo travel")
            elif travel_style == "couple" and cat in {"lakes", "viewpoints", "hills"}:
                score += 0.12
                reasons.append("Strong couple-trip fit")

            popularity = float(destination.average_rating or 0) * 0.025 + min(math.log10((destination.views_count or 0) + 1) * 0.015, 0.05)
            behavior = min(affinity.get(cat, 0) * 0.025, 0.10)
            score += popularity + behavior
            breakdown["community"] = round(popularity + behavior, 3)

            risk = getattr(destination, "risk_analysis", None)
            risk_level = (risk.risk_category or "low").lower() if risk else "low"
            # Avoid silently pushing high-risk places to the top, but keep them
            # available and explain the indicator in the result.
            historical_risk_adjustment = -0.08 if risk_level in {"high", "critical"} else 0.0
            score += historical_risk_adjustment
            breakdown["historical_risk_adjustment"] = historical_risk_adjustment

            warning = current_warning_by_destination.get(destination.id)
            current_warning_adjustment = 0.0
            availability = "available"
            if warning:
                current_warning_adjustment = {
                    "low": -0.02, "moderate": -0.10, "high": -0.28, "critical": -0.55,
                }.get(warning["severity"], 0.0)
                # Only a verified official/admin critical warning can mark a
                # destination temporarily unavailable; news/model rows cannot.
                if (
                    warning["severity"] == "critical" and warning["verified"]
                    and warning["source_type"] in {"official", "admin", "api"}
                ):
                    availability = "temporarily_unavailable"
                score += current_warning_adjustment
            breakdown["current_warning_adjustment"] = current_warning_adjustment

            service_count = destination.hospital_total + destination.police_total + destination.hotel_total
            emergency_score = min(service_count * 0.015, 0.09)
            score += emergency_score
            breakdown["services"] = round(emergency_score, 3)
            if destination.hospital_total and destination.police_total:
                reasons.append("Verified hospital and police coverage")

            route_records = list(destination.transit_routes.all())
            route_text = " ".join((route.road_condition or "") for route in route_records).lower()
            route_penalty = -0.10 if any(word in route_text for word in ["blocked", "closed", "landslide", "impassable", "dangerous"]) else 0.04 if route_records else 0.0
            score += route_penalty
            breakdown["route_condition"] = route_penalty
            safety_context = {
                "hospital_count": destination.hospital_total,
                "police_count": destination.police_total,
                "hotel_count": destination.hotel_total,
                "route_condition": route_records[0].road_condition if route_records else "No verified route condition",
                "availability": availability,
                "current_warning": {
                    "title": warning["title"], "severity": warning["severity"],
                    "verified": warning["verified"], "source_type": warning["source_type"],
                } if warning else None,
            }
            rows.append((score, destination, reasons[:5], breakdown, inferred_difficulty, inferred_budget, estimated_daily, risk_level, safety_context))

        # Diversity-aware reranking (MMR-style): preserve the existing score,
        # then progressively penalize repeated categories and districts.
        rows.sort(key=lambda row: (-row[0], row[1].id))
        pool = rows[: max(limit * 12, 120)]
        candidates, category_counts, district_counts = [], {}, {}
        target_count = min(len(pool), max(limit * 3, limit))
        while pool and len(candidates) < target_count:
            def diversity_score(row):
                destination = row[1]
                category = destination.category.slug if destination.category_id else "uncategorized"
                district = (destination.district or "unknown").lower()
                return row[0] - category_counts.get(category, 0) * 0.13 - district_counts.get(district, 0) * 0.035
            best = max(pool, key=diversity_score)
            pool.remove(best)
            candidates.append(best)
            chosen = best[1]
            category = chosen.category.slug if chosen.category_id else "uncategorized"
            district = (chosen.district or "unknown").lower()
            category_counts[category] = category_counts.get(category, 0) + 1
            district_counts[district] = district_counts.get(district, 0) + 1

        if candidates:
            max_score = max(row[0] for row in candidates) or 1
            candidates = [(max(0.0, row[0] / max_score), *row[1:]) for row in candidates]

        serialized = DestinationListSerializer(
            [row[1] for row in candidates], many=True, context={"request": request}
        ).data

        # Never show the same photo for two recommendation cards. If the
        # catalog resolves a duplicate, skip it and take the next ranked DB row.
        data, chosen_rows, used_images = [], [], set()
        for item, row in zip(serialized, candidates):
            image_key = (item.get("cover_image_url") or "").split("?")[0]
            if image_key and image_key in used_images:
                continue
            if image_key:
                used_images.add(image_key)
            score, destination, reasons, breakdown, inferred_difficulty, inferred_budget, estimated_daily, risk_level, safety_context = row
            item["ml_score"] = round(min(score, 1.0), 3)
            item["why_recommended"] = reasons or ["Strong overall match from the live destination catalog"]
            item["match_breakdown"] = breakdown
            item["difficulty"] = inferred_difficulty
            item["budget_level"] = inferred_budget
            item["budget_level_is_ranking_tag"] = True
            item["recommended_days"] = destination.recommended_days or 2
            item["risk_summary"] = {"level": risk_level, "label": "Historical/model indicator"}
            if destination.latitude is not None and destination.longitude is not None:
                from .emergency_service import build_emergency_directory
                nearby = build_emergency_directory(destination.latitude, destination.longitude, destination=destination, radius_km=100, limit=1)
                safety_context["nearest_hospital"] = nearby["hospitals"][0] if nearby["hospitals"] else None
                safety_context["nearest_police"] = nearby["police"][0] if nearby["police"] else None
            item["safety_context"] = safety_context
            item["data_source"] = destination.source or ("User submission" if destination.is_user_submitted else "Database")
            data.append(item)
            chosen_rows.append(row)
            if len(data) >= limit:
                break

        return Response({
            "source": "live_database_content_model", "model_version": "content-v2",
            "preferences": {"moods": moods, "days": days, "budget": budget, "difficulty": difficulty, "season": season, "travel_style": travel_style, "province": province},
            "count": len(data), "results": data,
        })



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
