from decimal import Decimal
from .phone_quality import usable_phone

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, F, Prefetch, Q, Value
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.views import View
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
    Alert, EmergencyContact, Notification, NotificationPreference, DeviceToken, Hotel, Hospital, PoliceStation,
    OSMEssentialService, OSMTourismPlace, DestinationAuditLog,
    TravelExpenseFeedback, TravelRiskFeedback, InfrastructureSubmission, InfrastructureMedia,
    CurrentHazard, RiskIncident, RiskObservation, RecommendationEvent, RiskNewsReport,
    SiteSetting, ManagedPage, ContentSection, ManagedNavigationItem, CMSContentTranslation, DestinationFeatureProfile, StaffCapabilityProfile,
    Restaurant, DestinationTransitRoute, TravelPlan, TravelPlanStop, HeroSlide,
    TravelerDocument, RedirectRule, NewsletterSignup, LocationHistory, SearchQuery, WebhookEndpoint, WebhookDelivery,
    UITranslation,
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsOwner, CanSubmitPlace, HasCapability, HasCapabilityOrReadOnly
from .serializers import (
    LanguageSerializer, CategorySerializer, DestinationListSerializer,
    DestinationDetailSerializer, DestinationWriteSerializer, DestinationApprovalSerializer,
    DestinationImageSerializer, DestinationVideoSerializer, DestinationTranslationSerializer,
    ReviewSerializer, RatingSerializer, FavoriteSerializer, VisitHistorySerializer, BudgetSerializer,
    AlertSerializer, EmergencyContactSerializer, NotificationSerializer, NotificationPreferenceSerializer, DeviceTokenSerializer,
    NearbyDestinationQuerySerializer, TranslateRequestSerializer, PhotoUploadSerializer, HotelSerializer, OSMEssentialServiceSerializer,
    UITranslationSerializer, UITranslationBulkSerializer,
    OSMTourismPlaceSerializer, TravelExpenseFeedbackSerializer, TravelRiskFeedbackSerializer,
    InfrastructureSubmissionSerializer, InfrastructureMediaSerializer, RiskNewsReportSerializer, DestinationFeatureProfileSerializer,
    RiskIncidentAdminSerializer, CurrentHazardAdminSerializer, RiskObservationAdminSerializer,
    RestaurantSerializer, DestinationTransitRouteSerializer, TravelPlanSerializer, TravelPlanStopSerializer,
    TravelerDocumentSerializer,
)
from .utils import public_media_url
from .utils import (
    haversine_distance, bounding_box, translate_text, notify_user,
    get_destination_photos, register_photo_view, get_current_weather, overpass_search_nearby,
    find_nearby_places, get_disaster_helplines,
)


def _invalidate_public_content_caches():
    from django.core.cache import cache
    cache.delete("dest:map-points:v1")
    cache.delete("seo:sitemap:v1")
    try:
        cache.incr("public_config_version")
    except Exception:
        import time
        cache.set("public_config_version", str(int(time.time())), 86400 * 30)


def _check_rate_limit(key_prefix, limit, period_seconds):
    """Simple rate limiting using Django's cache framework.

    Args:
        key_prefix: Prefix for the cache key (e.g., 'rate_limit_search')
        limit: Maximum number of requests allowed
        period_seconds: Time window in seconds

    Returns:
        tuple: (allowed: bool, remaining: int, reset_in: int)
    """
    cache_key = f"rate_limit:{key_prefix}"
    now = timezone.now().timestamp()

    # Get current window data
    window = cache.get(cache_key)
    if window is None:
        # First request in window
        cache.set(cache_key, {"count": 1, "reset_at": now + period_seconds}, period_seconds)
        return True, limit - 1, period_seconds

    # Check if window has expired
    if now > window["reset_at"]:
        # Reset window
        cache.set(cache_key, {"count": 1, "reset_at": now + period_seconds}, period_seconds)
        return True, limit - 1, period_seconds

    # Increment count
    window["count"] += 1
    remaining = max(0, limit - window["count"])
    reset_in = int(window["reset_at"] - now)

    if window["count"] > limit:
        return False, 0, reset_in

    cache.set(cache_key, window, reset_in)
    return True, remaining, reset_in


def _get_rate_limit_headers(allowed, remaining, reset_in):
    """Build rate limit headers."""
    return {
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_in),
    }


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
    
def _section_visible_for(vis, user, now):
    """Conditional content (date window + audience roles) enforced SERVER-SIDE
    so hidden sections never even reach the client. Device rules are the only
    part evaluated in the browser (the server cannot know the viewport)."""
    from datetime import date as _date
    if not isinstance(vis, dict):
        return True
    today = now.date()
    for key, compare in (("start_date", -1), ("end_date", 1)):
        raw = str(vis.get(key) or "").strip()
        if raw:
            try:
                bound = _date.fromisoformat(raw)
            except ValueError:
                continue
            if compare < 0 and today < bound:
                return False
            if compare > 0 and today > bound:
                return False
    roles = vis.get("roles") or []
    if isinstance(roles, list) and roles:
        role = "guest"
        if getattr(user, "is_authenticated", False):
            role = str(getattr(user, "role", None) or "tourist").lower()
        if role not in {str(r).lower() for r in roles}:
            return False
    return True


class PublicConfigView(APIView):
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import re
        now = timezone.now()
        from .cms_publishing import publish_due_pages, publish_due_sections
        publish_due_pages(now)
        publish_due_sections(now)
        language = request.query_params.get("lang", "en")
        if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", language):
            language = "en"
        translations = {(row.target_resource, row.object_id): row.content for row in
            CMSContentTranslation.objects.filter(language_code=language)} if language != "en" else {}
        pages = ManagedPage.objects.filter(is_enabled=True, status="published").prefetch_related("sections")
        page_rows = []
        for page in pages:
            page_translation = translations.get(("pages", page.id), {})
            # Published page metadata is frozen independently of the live
            # draft fields.  A partial/legacy snapshot is merged with safe
            # live fallbacks so old records remain readable.
            page_snap = page.published_snapshot if isinstance(page.published_snapshot, dict) else {}
            page_content = {
                "key": page.key, "route": page.route, "title": page.title,
                "meta_description": page.meta_description, "seo_title": page.seo_title,
                "og_image_url": page.og_image_url, "search_visible": page.search_visible,
                "is_enabled": page.is_enabled,
            }
            page_content.update(page_snap)
            sections = []
            for section in page.sections.filter(status="published"):
                # Snapshot isolation: once a section has been published through
                # the CMS, the public serves the frozen snapshot; later edits
                # stay drafts until the next Publish. Sections that predate
                # snapshots fall back to their live fields.
                snap = section.published_snapshot if isinstance(section.published_snapshot, dict) else None
                content = {
                    "title": section.title, "subtitle": section.subtitle, "body": section.body,
                    "image_url": section.image_url, "cta_text": section.cta_text, "cta_url": section.cta_url,
                    "icon": section.icon, "section_type": section.section_type,
                    "layout_variant": section.layout_variant,
                    "config": section.config if isinstance(section.config, dict) else {},
                    "display_order": section.display_order,
                }
                if snap:
                    content.update(snap)
                # Visibility is part of the frozen public state for new
                # snapshots; legacy snapshots without the key retain the
                # live value for compatibility.
                if not content.get("is_visible", section.is_visible):
                    continue
                section_config = content.get("config") if isinstance(content.get("config"), dict) else {}
                if not _section_visible_for(section_config.get("visibility"), request.user, now):
                    continue
                translated = translations.get(("sections", section.id), {})
                if snap and isinstance(snap.get("blocks"), list):
                    blocks = snap.get("blocks") or []
                else:
                    blocks = [
                        {
                            "id": b.id, "block_type": b.block_type, "title": b.title,
                            "position": b.position, "data": b.data, "is_visible": b.is_visible
                        }
                        for b in section.blocks.filter(is_visible=True).order_by("position", "id")
                    ]
                sections.append({
                    "id": section.id, "key": section.key,
                    "title": translated.get("title", content.get("title", "")),
                    "subtitle": translated.get("subtitle", content.get("subtitle", "")),
                    "body": translated.get("body", content.get("body", "")),
                    "image_url": content.get("image_url", ""),
                    "cta_text": translated.get("cta_text", content.get("cta_text", "")),
                    "cta_url": content.get("cta_url", ""), "icon": content.get("icon", ""),
                    "section_type": content.get("section_type", "text"),
                    "layout_variant": content.get("layout_variant", "default"),
                    "config": section_config, "display_order": content.get("display_order", 0),
                    "blocks": blocks,
                })
            page_rows.append({
                "id": page.id, "key": page_content.get("key", page.key),
                "route": page_content.get("route", page.route),
                "title": page_translation.get("title", page_content.get("title", page.title)),
                "seo_title": page_content.get("seo_title", ""),
                "og_image_url": page_content.get("og_image_url", ""),
                "search_visible": page_content.get("search_visible", True),
                "meta_description": page_translation.get("meta_description", page_content.get("meta_description", "")),
                "sections": sections,
            })
        navigation = []
        for item in ManagedNavigationItem.objects.filter(is_active=True):
            allowed_roles = item.allowed_roles if isinstance(item.allowed_roles, list) else []
            if allowed_roles:
                current_role = "guest" if not getattr(request.user, "is_authenticated", False) else str(getattr(request.user, "role", "tourist") or "tourist").lower()
                if current_role not in {str(role).lower() for role in allowed_roles}:
                    continue
            translated = translations.get(("navigation", item.id), {})
            navigation.append({"id": item.id, "location": item.location,
                "label": translated.get("label", item.label), "route": item.route, "icon": item.icon,
                "parent_id": item.parent_id, "allowed_roles": item.allowed_roles, "display_order": item.display_order})
        from .notices import active_notices_qs, serialize_notice
        notices = [serialize_notice(notice) for notice in active_notices_qs(now)[:20]]
        public_dests = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        catalog = {
            "destination_count": public_dests.count(),
            "featured_count": public_dests.filter(is_featured=True).count(),
            "province_count": 7,
            "note": "Counts are live recorded destinations. Visitor totals are not stored.",
        }
        hero_slides = [
            {
                "id": s.id, "title": s.title, "kicker": s.kicker, "subtitle": s.subtitle,
                "tagline": s.tagline, "link_slug": s.link_slug,
                "image": s.resolve_image(request=request),
                "overlay": s.overlay_strength, "focal_point": s.focal_point,
                "duration": s.duration_seconds,
            }
            for s in HeroSlide.objects.filter(is_active=True).order_by("order", "id")
        ]
        redirects = [{"old_path": r.old_path, "new_path": r.new_path, "permanent": r.is_permanent}
            for r in RedirectRule.objects.filter(is_active=True)]
        return Response({"mapillary_access_token": settings.MAPILLARY_ACCESS_TOKEN, "language": language,
            # OAuth client IDs are public values (the same ones you'd put in
            # VITE_*_CLIENT_ID); exposing them means one backend .env update
            # enables the Google/GitHub buttons without touching the frontend.
            "oauth_client_ids": {"google": settings.GOOGLE_CLIENT_ID, "github": settings.GITHUB_CLIENT_ID},
            "settings": {item.key: item.value for item in SiteSetting.objects.filter(is_public=True)},
            "pages": page_rows, "navigation": navigation, "notices": notices, "catalog": catalog,
            "hero_slides": hero_slides, "redirects": redirects})


class NewsletterSubscribeView(APIView):
    """Public footer newsletter signup — stores the email, never fakes success."""
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import re
        email = str(request.data.get("email", "")).strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
            return Response({"detail": "Enter a valid email address"}, status=status.HTTP_400_BAD_REQUEST)
        _, created = NewsletterSignup.objects.get_or_create(email=email)
        if not created:
            NewsletterSignup.objects.filter(email=email, is_active=False).update(is_active=True)
        # Same wording either way, so the form cannot reveal who is subscribed.
        return Response(
            {"message": "Thanks. You'll get occasional travel notes at this address. You can unsubscribe at any time from the Unsubscribe page or the link in any newsletter."},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DiscoverNepalView(APIView):
    """Recorded destinations and published notices for the Discover Nepal page."""
    serializer_class = None

    permission_classes = [permissions.AllowAny]
    PENDING = "Not recorded — we will update soon"

    def _group(self, queryset, limit=12):
        items = list(queryset[:limit])
        return {
            "items": DestinationListSerializer(items, many=True, context={"request": self.request}).data,
            "count": queryset.count(),
            "pending": not items,
            "message": None if items else self.PENDING,
        }

    def get(self, request):
        from .models import VisitorNotice
        from .notices import serialize_notice

        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        ).select_related("category").prefetch_related("gallery")
        wildlife = qs.filter(
            Q(name__icontains="national park") | Q(name__icontains="conservation")
            | Q(name__icontains="wildlife") | Q(name__icontains="reserve")
            | Q(type__icontains="wildlife") | Q(category__slug__icontains="wildlife")
            | Q(category__name__icontains="wildlife")
        )
        heritage = qs.filter(
            Q(name__icontains="durbar") | Q(name__icontains="unesco")
            | Q(name__icontains="heritage") | Q(name__icontains="stupa")
            | Q(type__icontains="heritage") | Q(category__slug__icontains="heritage")
            | Q(category__name__icontains="heritage")
        )
        mountains = qs.filter(
            Q(name__icontains="base camp") | Q(name__icontains="himal")
            | Q(name__icontains="peak") | Q(type__icontains="mountain")
            | Q(category__slug__icontains="mountain") | Q(category__name__icontains="mountain")
        )
        # Primary signal: curated text fields. Fallback signal: the real
        # category taxonomy (Cultural & Ethnic Tourism / Food & Culinary /
        # Festivals & Events) so recorded destinations surface even when the
        # long-form fields are still empty.
        # Exact slugs only: substring matching on "culture"/"cultural" also
        # catches "agriculture" / "Agricultural & Farm Tourism", which put
        # poultry farms in the heritage section.
        culture_slugs = {"culture", "heritage-temples", "museums",
                         "buddhist-sites", "pilgrimage", "religious-sites"}
        culture = qs.filter(
            (~Q(cultural_significance__isnull=True) & ~Q(cultural_significance=""))
            | Q(category__slug__in=culture_slugs)
        ).distinct()
        cuisine = qs.filter(
            (~Q(food_cuisine_info__isnull=True) & ~Q(food_cuisine_info=""))
            | Q(category__slug__in={"food-culinary"})
        ).distinct()
        featured = qs.filter(is_featured=True).order_by("-average_rating", "name")
        if not featured.exists():
            featured = qs.order_by("-average_rating", "-views_count", "name")

        notices = VisitorNotice.objects.filter(is_published=True, kind=VisitorNotice.Kind.FESTIVAL).order_by("-starts_at")[:12]
        festival_items = [serialize_notice(notice) for notice in notices]
        if not festival_items:
            # No curated festival notices yet: fall back to destinations in
            # the recorded Festivals & Events category, in notice shape so the
            # public page renders them identically.
            from .location_sync import display_city
            fallback_qs = qs.filter(
                Q(category__slug__in={"festivals"})
            ).order_by("-average_rating", "name")[:8]
            festival_items = [{
                "id": d.id,
                "kind": "festival",
                "title": d.name,
                "body": d.short_description or (d.description or "")[:160],
                "city": display_city(d) or "",
                "district": d.district or "",
                "destination_id": d.id,
                "destination_name": d.name,
                "destination_slug": d.slug,
                "starts_at": None,
                "ends_at": None,
            } for d in fallback_qs]

        provinces = []
        for name in ("Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"):
            province_qs = qs.filter(province__icontains=name)
            sample = province_qs.order_by("-is_featured", "-average_rating", "name").first()
            from .location_sync import display_city
            provinces.append({
                "name": name,
                "destination_count": province_qs.count(),
                "sample_name": sample.name if sample else None,
                "sample_slug": sample.slug if sample else None,
                "sample_city": (sample and (display_city(sample) or sample.district)) or None,
            })

        return Response({
            "pending_label": self.PENDING,
            "catalog": {
                "destination_count": qs.count(),
                "featured_count": qs.filter(is_featured=True).count(),
            },
            "featured": self._group(featured, 12),
            "wildlife": self._group(wildlife.order_by("-average_rating", "name"), 12),
            "heritage": self._group(heritage.order_by("-average_rating", "name"), 16),
            "mountains": self._group(mountains.order_by("-average_rating", "name"), 16),
            "culture": self._group(culture.order_by("-average_rating", "name"), 12),
            "cuisine": self._group(cuisine.order_by("-average_rating", "name"), 8),
            "festivals": {
                "items": festival_items,
                "count": len(festival_items),
                "pending": not festival_items,
                "message": None if festival_items else self.PENDING,
            },
            "provinces": provinces,
        })


class TranslateTextView(APIView):
    """
    POST /api/v1/translate/  {"text": "...", "target_language": "ne",
                             "source_language": "auto" (optional)}

    FIX: the URLconf referenced this view but it was never defined, which
    crashed the whole `tourist.urls` import (AttributeError: module
    'tourist.views' has no attribute 'TranslateTextView').
    """
    serializer_class = None
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


class UITranslationListView(APIView):
    """GET /api/v1/translation/ui-strings/?lang=ne — public.

    Returns {key: value} for the requested language so the SPA can
    merge admin edits over its bundled dictionary.
    """
    serializer_class = UITranslationSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lang = (request.query_params.get("lang") or "").strip().lower()
        if not lang:
            return Response({"detail": "Query param 'lang' is required."}, status=400)
        rows = UITranslation.objects.filter(language=lang).exclude(value="").values("key", "value")
        return Response({row["key"]: row["value"] for row in rows})


class UITranslationBulkView(APIView):
    """POST /api/v1/translation/ui-strings/bulk/ — staff only.

    Upserts [{key, language, value}]. Blank value deletes the override
    (frontend falls back to the bundled string).
    """
    serializer_class = UITranslationBulkSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        items = request.data if isinstance(request.data, list) else request.data.get("items", [])
        serializer = UITranslationBulkSerializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)
        saved = 0
        for item in serializer.validated_data:
            value = (item["value"] or "").strip()
            if not value:
                UITranslation.objects.filter(key=item["key"], language=item["language"]).delete()
                continue
            UITranslation.objects.update_or_create(
                key=item["key"],
                language=item["language"],
                defaults={"value": value, "updated_by": request.user},
            )
            saved += 1
        return Response({"saved": saved})


class AdminImageManagerView(APIView):
    """Admin CMS image management — search, add, update, remove images.

    GET  /api/v1/admin/image-manager/?q=pokhara — search destinations/hotels
    POST /api/v1/admin/image-manager/add/ — add image to destination/hotel
    POST /api/v1/admin/image-manager/update/ — update image metadata
    POST /api/v1/admin/image-manager/remove/ — remove image
    """
    serializer_class = None
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"detail": "Query param 'q' is required."}, status=400)

        from tourist.utils import haversine_distance
        from tourist.models import EmergencyContact, Hospital, PoliceStation

        # Search destinations
        destinations = Destination.objects.filter(
            models.Q(name__icontains=q) | models.Q(district__icontains=q)
        ).annotate(img_count=models.Count("gallery"))[:20]

        # Search hotels
        hotels = Hotel.objects.filter(
            models.Q(name__icontains=q) | models.Q(destination__name__icontains=q)
        )[:20]

        dest_list = []
        for d in destinations:
            # Nearby places (within 50km)
            nearby = []
            if d.latitude and d.longitude:
                for other in Destination.objects.filter(is_active=True).exclude(id=d.id):
                    if other.latitude and other.longitude:
                        dist = haversine_distance(
                            float(d.latitude), float(d.longitude),
                            float(other.latitude), float(other.longitude)
                        )
                        if dist <= 50:
                            nearby.append({
                                "id": other.id,
                                "name": other.name,
                                "distance_km": round(dist, 1),
                            })
                nearby.sort(key=lambda x: x["distance_km"])
                nearby = nearby[:10]

            # Emergency contacts
            emergency = []
            if d.latitude and d.longitude:
                for h in Hospital.objects.all():
                    if h.latitude and h.longitude:
                        dist = haversine_distance(
                            float(d.latitude), float(d.longitude),
                            float(h.latitude), float(h.longitude)
                        )
                        if dist <= 50:
                            emergency.append({
                                "type": "hospital",
                                "name": h.name,
                                "phone": h.phone,
                                "distance_km": round(dist, 1),
                            })
                for p in PoliceStation.objects.all():
                    if p.latitude and p.longitude:
                        dist = haversine_distance(
                            float(d.latitude), float(d.longitude),
                            float(p.latitude), float(p.longitude)
                        )
                        if dist <= 50:
                            emergency.append({
                                "type": "police",
                                "name": p.name,
                                "phone": p.phone,
                                "distance_km": round(dist, 1),
                            })
                emergency.sort(key=lambda x: x["distance_km"])
                emergency = emergency[:10]

            dest_list.append({
                "id": d.id,
                "name": d.name,
                "slug": d.slug,
                "district": d.district,
                "description": d.description or "",
                "short_description": d.short_description or "",
                "latitude": str(d.latitude) if d.latitude else None,
                "longitude": str(d.longitude) if d.longitude else None,
                "image_count": d.img_count,
                "images": [
                    {
                        "id": img.id,
                        "url": img.external_url or (img.image.url if img.image else ""),
                        "is_cover": img.is_cover,
                        "verification_status": img.verification_status,
                        "photographer": img.photographer,
                        "license_type": img.license_type,
                    }
                    for img in d.gallery.all()[:5]
                ],
                "nearby_places": nearby,
                "emergency_services": emergency,
            })

        return Response({
            "destinations": dest_list,
            "hotels": [
                {
                    "id": h.id,
                    "name": h.name,
                    "destination": h.destination.name if h.destination else "",
                    "cover_image": h.cover_image if h.cover_image else "",
                    "external_image_url": h.external_image_url if h.external_image_url else "",
                }
                for h in hotels
            ],
        })

    def post(self, request):
        action = request.data.get("action")
        if action == "add":
            return self._add_image(request)
        elif action == "update":
            return self._update_image(request)
        elif action == "remove":
            return self._remove_image(request)
        elif action == "edit_destination":
            return self._edit_destination(request)
        return Response({"detail": "Invalid action. Use: add, update, remove, edit_destination"}, status=400)

    def _edit_destination(self, request):
        dest_id = request.data.get("destination_id")
        name = request.data.get("name")
        district = request.data.get("district")
        description = request.data.get("description")
        short_description = request.data.get("short_description")

        dest = Destination.objects.filter(pk=dest_id).first()
        if not dest:
            return Response({"detail": "Destination not found"}, status=404)

        if name is not None:
            dest.name = name
        if district is not None:
            dest.district = district
        if description is not None:
            dest.description = description
        if short_description is not None:
            dest.short_description = short_description

        dest.save()
        return Response({"id": dest.id, "name": dest.name, "detail": "Destination updated"})

    def _add_image(self, request):
        dest_id = request.data.get("destination_id")
        image_url = request.data.get("image_url")
        is_cover = request.data.get("is_cover", False)

        if not dest_id or not image_url:
            return Response({"detail": "destination_id and image_url required"}, status=400)

        dest = Destination.objects.filter(pk=dest_id).first()
        if not dest:
            return Response({"detail": "Destination not found"}, status=404)

        img = DestinationImage.objects.create(
            destination=dest,
            external_url=image_url,
            source=DestinationImage.Source.WIKIMEDIA,
            source_platform="Admin CMS",
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
            is_cover=is_cover,
        )
        return Response({"id": img.id, "detail": "Image added"})

    def _update_image(self, request):
        image_id = request.data.get("image_id")
        is_cover = request.data.get("is_cover")
        verification_status = request.data.get("verification_status")

        img = DestinationImage.objects.filter(pk=image_id).first()
        if not img:
            return Response({"detail": "Image not found"}, status=404)

        if is_cover is not None:
            img.is_cover = is_cover
        if verification_status:
            img.verification_status = verification_status
        img.save()
        return Response({"id": img.id, "detail": "Image updated"})

    def _remove_image(self, request):
        image_id = request.data.get("image_id")
        img = DestinationImage.objects.filter(pk=image_id).first()
        if not img:
            return Response({"detail": "Image not found"}, status=404)

        img.delete()
        return Response({"detail": "Image removed"})


class TravelGuideListView(APIView):
    """GET /api/v1/travel-guides/ — public.

    Returns all published guides with basic info for the city selector.
    """
    # Response is a hand-built list of dicts, so there is no model serializer
    # for drf-spectacular to infer. See TravelGuideDetailView.
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        guides = TravelGuide.objects.filter(is_published=True).select_related("destination")
        return Response([
            {
                "slug": g.slug,
                "title": g.title,
                "days_count": g.days_count,
                "destination_name": g.destination.name,
                "destination_slug": g.destination.slug,
            }
            for g in guides
        ])


class TravelGuideDetailView(APIView):
    """GET /api/v1/travel-guides/<slug>/ — public.

    Returns the guide with all days, linked hotels, hospitals and
    attractions (names, slugs, coordinates) so the frontend can render
    a full itinerary page with real data.
    """
    # Response is assembled by hand from the guide's days plus related hotels,
    # hospitals and attractions, so there is no single model serializer for
    # drf-spectacular to infer. Declaring it explicitly keeps the operation in
    # the OpenAPI document instead of logging "unable to guess serializer".
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        from .models import Destination, TravelGuide

        guide = TravelGuide.objects.select_related("destination").filter(
            slug=slug,
            is_published=True,
            destination__is_active=True,
            destination__status=Destination.SubmissionStatus.APPROVED,
        ).first()
        if not guide:
            return Response({"detail": "Guide not found."}, status=404)

        days = []
        for day in guide.days.all():
            days.append({
                "day_number": day.day_number,
                "title": day.title,
                "description": day.description,
                "route": day.route,
                "travel_distance": day.travel_distance,
                "travel_time": day.travel_time,
                "overnight_stay": day.overnight_stay,
                "morning": day.morning,
                "afternoon": day.afternoon,
                "evening": day.evening,
                "practical_notes": day.practical_notes,
                "hotels": [
                    {"id": h.id, "name": h.name, "address": h.address,
                     "price_per_night": str(h.price_per_night) if h.price_per_night else None,
                     "rating": h.rating, "booking_status": h.booking_status,
                     "source_url": h.source_url, "website": h.website}
                    for h in day.hotels.filter(
                        is_verified=True,
                        is_active=True,
                        archived_at__isnull=True,
                    ).exclude(source_url="")
                ],
                "hospitals": [
                    {"id": h.id, "name": h.name, "address": h.address,
                     "phone": h.phone, "opening_hours": h.opening_hours,
                     "source_url": h.source_url, "website": h.website}
                    for h in day.hospitals.filter(
                        is_verified=True,
                        is_archived=False,
                    ).exclude(source_url="")
                ],
                "attractions": [
                    {"id": a.id, "name": a.name, "slug": a.slug,
                     "latitude": str(a.latitude) if a.latitude is not None else None,
                     "longitude": str(a.longitude) if a.longitude is not None else None}
                    for a in day.attractions.filter(
                        is_active=True,
                        status=Destination.SubmissionStatus.APPROVED,
                    )
                ],
            })

        return Response({
            "slug": guide.slug,
            "title": guide.title,
            "subtitle": guide.subtitle,
            "days_count": guide.days_count,
            "pace": guide.pace,
            "best_for": guide.best_for,
            "destination": {
                "id": guide.destination.id,
                "name": guide.destination.name,
                "slug": guide.destination.slug,
            },
            "days": days,
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
    queryset = Destination.objects.select_related("category", "created_by").prefetch_related(Prefetch("gallery", queryset=DestinationImage.objects.select_related("uploaded_by")))
    permission_classes = [CanSubmitPlace]
    filterset_class = DestinationFilter
    search_fields = ["name", "description", "city", "country"]
    ordering_fields = ["average_rating", "entry_fee", "created_at", "name", "views_count", "is_featured"]
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
        if user.is_authenticated and (user.is_superuser or (user.is_staff and user.role in {"admin", "super_admin", "tourism_admin"})):
            return qs
        if user.is_authenticated:
            # Canonical public rule + this user's own submissions (any status)
            from django.db.models import Q
            public_ids = Destination.publicly_visible(qs).values("id")
            qs = qs.filter(Q(id__in=public_ids) | Q(created_by=user))
        else:
            qs = Destination.publicly_visible(qs)

        # The public destination catalogue is for places to visit. Hotels,
        # inns, hostels, restaurants and service points have their own APIs.
        # Previously this filter only ran when type=attraction, so a category
        # such as "mountains" could surface "The North Face Inn" and "1 Room".
        if self.action == "list":
            requested_type = (self.request.query_params.get("type") or "").lower()
            from .filters import (
                ACCOMMODATION_SLUGS, ACCOMMODATION_NAME_HINTS,
                NON_ATTRACTION_SLUGS, NON_ATTRACTION_NAME_HINTS,
            )
            if requested_type not in ("hotel", "hotels", "accommodation"):
                exclude_slugs = set(ACCOMMODATION_SLUGS) | set(NON_ATTRACTION_SLUGS)
                qs = qs.exclude(category__slug__in=exclude_slugs)
                for hint in ACCOMMODATION_NAME_HINTS:
                    qs = qs.exclude(name__icontains=hint)
                for hint in NON_ATTRACTION_NAME_HINTS:
                    qs = qs.exclude(name__icontains=hint)
        return qs

    def filter_queryset(self, queryset):
        """Rank text-search results by how well the *name* matches.

        DRF's SearchFilter only filters, so a search for "pokhara" used to
        return whatever matched first in the default order (a gorge that
        mentions Pokhara in its description). When the caller searches without
        choosing an explicit ordering, exact names come first, then names that
        start with the term, then names that contain it, then city/district
        matches, then description-only matches.
        """
        queryset = super().filter_queryset(queryset)
        term = (self.request.query_params.get("search") or "").strip()
        if not term or self.request.query_params.get("ordering"):
            return queryset
        from django.db.models import Case, IntegerField, Value, When
        import re
        from django.db import connection
        from django.db.models.functions import Length
        # Imported data files some lodgings as destinations ("Lumbini Boys
        # Hostel" under Buddhist Sites). They stay searchable, but a search for
        # a place should list the place and its sights before accommodation.
        boundary = r"\y" if connection.vendor == "postgresql" else r"\b"
        lodging = boundary + r"(hotel|hotwl|guest ?house|hostel|lodge|resort|homestay|home ?stay|apartment|inn|restaurant|cafe)s?" + boundary
        return queryset.annotate(
            _search_rank=Case(
                When(name__iexact=term, then=Value(0)),
                # "Pokhara Valley" (whole word) before "Pokharathok" (prefix).
                When(name__iregex=r"^" + re.escape(term) + boundary, then=Value(1)),
                When(name__istartswith=term, then=Value(2)),
                When(name__icontains=term, then=Value(3)),
                When(Q(city__icontains=term) | Q(district__icontains=term), then=Value(4)),
                default=Value(5),
                output_field=IntegerField(),
            ),
            _lodging=Case(When(name__iregex=lodging, then=Value(1)), default=Value(0), output_field=IntegerField()),
            _name_len=Length("name"),
        ).order_by("_search_rank", "_lodging", "-is_featured", "-average_rating", "_name_len", "name")

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
        # Filter/rank lightweight coordinate rows first. Loading each model's
        # gallery before pagination made a normal 12-card page prefetch photos
        # for thousands of destinations in the 250 km bounding box.
        candidates = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
            latitude__gte=box["min_lat"], latitude__lte=box["max_lat"],
            longitude__gte=box["min_lon"], longitude__lte=box["max_lon"],
        ).values_list("id", "latitude", "longitude")

        results = []
        for destination_id, dest_lat, dest_lon in candidates.iterator(chunk_size=1000):
            distance = haversine_distance(lat, lon, dest_lat, dest_lon)
            if distance <= radius_km:
                results.append((distance, destination_id))
        results.sort(key=lambda pair: (pair[0], pair[1]))
        destination_ids = [destination_id for _, destination_id in results]

        page = self.paginate_queryset(destination_ids)
        page_ids = list(page if page is not None else destination_ids)
        destinations_by_id = {
            destination.pk: destination
            for destination in Destination.objects.filter(pk__in=page_ids)
            .select_related("category")
            .prefetch_related("gallery")
        }
        destinations = [destinations_by_id[pk] for pk in page_ids if pk in destinations_by_id]
        serializer = DestinationListSerializer(
            destinations, many=True, context={"request": request, "user_lat": lat, "user_lon": lon}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny], url_path="map-points")
    def map_points(self, request):
        """
        Lightweight ALL-destinations feed for the distance/map explorer:
        every active approved destination that has coordinates, as
        {id, slug, name, district, province, latitude, longitude, category}.
        No photos, no descriptions — sized for plotting 6,000+ markers.
        Cached 5 minutes (the set changes slowly).
        """
        from django.core.cache import cache
        cache_key = "dest:map-points:v1"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
            latitude__isnull=False, longitude__isnull=False,
        ).select_related("category").order_by("name").values(
            "id", "slug", "name", "district", "province",
            "latitude", "longitude", "category__name")
        points = [{
            "id": r["id"], "slug": r["slug"], "name": r["name"],
            "district": r["district"] or "", "province": r["province"] or "",
            "latitude": float(r["latitude"]), "longitude": float(r["longitude"]),
            "category": r["category__name"] or "",
        } for r in qs.iterator(chunk_size=1000)]
        payload = {"count": len(points), "points": points}
        cache.set(cache_key, payload, 300)
        return Response(payload)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny], url_path="all-with-distances")
    def all_with_distances(self, request):
        """
        GET /api/v1/destinations/all-with-distances/?latitude=27.7172&longitude=85.324&transport_mode=Private+Car+/+Taxi

        Returns ALL approved destinations with exact distance_km (straight-line),
        estimated duration, and ETA based on transport mode.
        Results sorted by distance (nearest first).
        """
        query_serializer = NearbyDestinationQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        lat = query_serializer.validated_data["latitude"]
        lon = query_serializer.validated_data["longitude"]
        transport_mode = request.query_params.get("transport_mode", "Private Car / Taxi")
        limit = min(int(request.query_params.get("limit", 100)), 200)

        # Transport mode speeds (km/h)
        speeds = {
            "Private Car / Taxi": 35,
            "Tourist Bus": 28,
            "Motorcycle": 40,
            "Walking / Trek": 4.5,
            "Flight": 500,
        }
        speed = speeds.get(transport_mode, 35)

        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
            latitude__isnull=False, longitude__isnull=False,
        ).select_related("category").order_by("name")

        results = []
        for dest in qs.iterator(chunk_size=1000):
            distance = haversine_distance(lat, lon, dest.latitude, dest.longitude)
            if distance is None:
                continue
            # Estimate duration based on straight-line * road factor / speed
            road_factor = 1.25  # Typical road factor
            estimated_km = distance * road_factor
            duration_hours = estimated_km / speed
            total_minutes = round(duration_hours * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60

            eta_display = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} min"

            results.append({
                "id": dest.id,
                "slug": dest.slug,
                "name": dest.name,
                "district": dest.district or "",
                "province": dest.province or "",
                "category": dest.category.name if dest.category_id else "",
                "latitude": float(dest.latitude),
                "longitude": float(dest.longitude),
                "distance_km": round(distance, 2),
                "estimated_road_km": round(estimated_km, 2),
                "duration_min": total_minutes,
                "duration_display": eta_display,
                "transport_mode": transport_mode,
                "altitude": dest.altitude,
                "short_description": dest.short_description,
                "average_rating": float(dest.average_rating) if dest.average_rating else None,
            })

        # Sort by distance (nearest first)
        results.sort(key=lambda x: x["distance_km"])
        results = results[:limit]

        return Response({
            "count": len(results),
            "origin": {"latitude": lat, "longitude": lon},
            "transport_mode": transport_mode,
            "speed_kmh": speed,
            "road_factor": 1.25,
            "note": "Distances are straight-line (haversine). Road distances estimated with 1.25x factor. ETA based on average speeds.",
            "results": results
        })


    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.AllowAny])
    def translate(self, request, slug=None):
        """Translated name/description for this destination.

        Cache-first: serves the stored DestinationTranslation when the
        source text hasn't changed since it was made. Only machine-
        translates (and stores) when missing or stale. Human-edited
        rows (is_auto_generated=False) are never overwritten.
        """
        destination = self.get_object()
        target_lang = (
            request.query_params.get("language_code")
            or request.data.get("language_code")
            or request.data.get("target_language")
        )
        if not target_lang:
            return Response({"detail": "language_code is required."}, status=status.HTTP_400_BAD_REQUEST)
        if target_lang == "en":
            return Response({
                "name": destination.name,
                "description": destination.description,
                "short_description": destination.short_description,
            })

        language = get_object_or_404(Language, code=target_lang)
        translation, _ = DestinationTranslation.objects.get_or_create(
            destination=destination, language=language,
            defaults={"name": destination.name, "description": destination.description,
                      "short_description": destination.short_description},
        )
        source_sig = f"{destination.name}\n{destination.description}\n{destination.short_description}"
        stored_sig = f"{translation.name}\n{translation.description}\n{translation.short_description}"
        # Refresh when: never translated (still equal to source), source
        # changed and row is auto-generated, or explicitly re-requested.
        needs_refresh = (
            request.query_params.get("refresh") == "1"
            or stored_sig == f"{destination.name}\n{destination.description}\n{destination.short_description}"
            and translation.is_auto_generated
        )
        if needs_refresh and translation.is_auto_generated:
            try:
                translation.name = translate_text(destination.name, target_lang) or destination.name
                translation.description = translate_text(destination.description, target_lang) or destination.description
                translation.short_description = translate_text(destination.short_description, target_lang) or destination.short_description
                translation.is_auto_generated = True
                translation.save()
            except Exception:  # noqa: BLE001 - serve stale/source on MT failure
                pass
        return Response(DestinationTranslationSerializer(translation).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, slug=None):
        """Capability-scoped approval for a tourist-submitted place."""
        from .views_admin import _require_capability, _require_destination_access
        _require_capability(request, "destinations", "approve")
        destination = Destination.objects.filter(slug=slug).first() if slug else Destination.objects.filter(pk=self.kwargs.get("pk")).first()
        if not destination:
            return Response({"detail": "Destination not found."}, status=404)
        _require_destination_access(request, destination, "destinations", "approve")
        previous_status = destination.status
        serializer = DestinationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destination.status = serializer.validated_data["status"]
        destination.review_note = serializer.validated_data.get("review_note", "")
        destination.is_active = destination.status == Destination.SubmissionStatus.APPROVED
        if destination.status == Destination.SubmissionStatus.APPROVED:
            missing = []
            if not (destination.name or "").strip(): missing.append("name")
            if not (destination.description or "").strip(): missing.append("description")
            if destination.latitude is None or destination.longitude is None: missing.append("coordinates")
            if missing:
                return Response({"detail": f"Cannot publish: missing {', '.join(missing)}."}, status=400)
        destination.save(update_fields=["status", "review_note", "is_active", "updated_at"])
        _invalidate_public_content_caches()

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
        GET  — the destination's reviewed photo gallery. Public reads are
               side-effect free; discovery/acquisition is an explicit staff
               action through the media APIs.
        POST — authenticated contributors may submit a photo; it is tagged as
               a community candidate and remains private until moderation.
        """
        destination = self.get_object()
        if request.user.is_authenticated and request.user.is_staff:
            from .views_admin import _require_destination_access
            _require_destination_access(request, destination, "images", "add")
        elif not Destination.publicly_visible(Destination.objects.filter(pk=destination.pk)).exists():
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            serializer = PhotoUploadSerializer(data={**request.data, "destination": destination.id}, context={"request": request})
            serializer.is_valid(raise_exception=True)
            photo = serializer.save()
            return Response(DestinationImageSerializer(photo, context={"request": request}).data, status=status.HTTP_201_CREATED)

        photos = get_destination_photos(destination)
        # Public reads do not acquire media or write impression events.
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
    Looks a place up in the catalogue (exact/alias/substring match) and returns
    close suggestions otherwise. It never creates or approves records -- new
    places go through the reviewed submission workflow with a real source.
    """
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .views_admin import _require_capability
        _require_capability(request, "destinations", "add")
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"detail": "Query destination name is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .research_engine import research_and_build_destination
        from .views_admin import _has_capability, _is_platform_admin
        auto_publish = _is_platform_admin(request.user) and _has_capability(request, "destinations", "approve")
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
    serializer_class = None
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
        )
        matches = Destination.publicly_visible(matches)[:10]

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

    def get_queryset(self):
        queryset = super().get_queryset().select_related("destination")
        if self.request.method in permissions.SAFE_METHODS:
            user = self.request.user
            is_platform = bool(user.is_authenticated and (user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}))
            if not is_platform:
                queryset = queryset.filter(
                    verification_status="approved", is_verified=True,
                    destination__is_active=True,
                    destination__status=Destination.SubmissionStatus.APPROVED,
                )
                if user.is_authenticated:
                    from .views_admin import _scope_destination_queryset
                    queryset = queryset.filter(destination_id__in=_scope_destination_queryset(Destination.objects.all(), user).values("id"))
            elif user.is_authenticated:
                from .views_admin import _scope_destination_queryset
                queryset = queryset.filter(destination_id__in=_scope_destination_queryset(Destination.objects.all(), user).values("id"))
        return queryset

    def perform_create(self, serializer):
        destination = serializer.validated_data.get("destination")
        if destination is not None:
            from .views_admin import _require_destination_access
            _require_destination_access(self.request, destination, "images", "add")
        serializer.save(
            verification_status=DestinationImage.ImageStatus.PENDING,
            is_verified=False,
            source=DestinationImage.Source.USER_UPLOAD,
        )


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
        queryset=Hotel.objects.select_related("destination").prefetch_related("destination__gallery").order_by("-is_verified", "name", "id")
        user=self.request.user
        is_platform_admin = bool(user.is_authenticated and (user.is_superuser or user.role in {"admin","super_admin","tourism_admin"}))
        if self.request.method in permissions.SAFE_METHODS and not is_platform_admin:
            queryset=queryset.filter(is_active=True)
        if user.is_authenticated and user.is_staff and not is_platform_admin:
            from admin_panel.models import HotelAssignment
            assigned_ids = HotelAssignment.objects.filter(admin=user).values_list("hotel_id", flat=True)
            queryset = queryset.filter(id__in=assigned_ids)
        return queryset

    def perform_create(self, serializer):
        request = self.request
        user = request.user
        is_platform_admin = bool(user.is_authenticated and (user.is_superuser or user.role in {"admin","super_admin","tourism_admin"}))
        if not is_platform_admin:
            from admin_panel.models import HotelAssignment
            destination = serializer.validated_data.get("destination")
            destination_id = getattr(destination, "id", destination)
            if not HotelAssignment.objects.filter(admin=user, hotel__destination_id=destination_id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You may only create hotels in an assigned destination")
        serializer.save(source=Hotel.Source.MANUAL)
        _invalidate_public_content_caches()

    def perform_update(self, serializer):
        if any(field in self.request.data for field in ("is_verified", "verified_at")):
            from .views_admin import _require_capability
            _require_capability(self.request, "hotels", "approve")
        before = {field: getattr(serializer.instance, field, None) for field in ("name", "address", "price_per_night", "booking_status", "is_active")}
        hotel = serializer.save()
        _invalidate_public_content_caches()
        from audit.logging_services import log_action
        log_action(request=self.request, action="hotel.update", category="hotels", message=f"Hotel '{hotel.name}' updated", object_type="Hotel", object_id=str(hotel.id), extra={"before": before})

    def perform_destroy(self, instance):
        instance.is_active=False;instance.archived_at=timezone.now();instance.booking_status=Hotel.BookingStatus.UNAVAILABLE
        instance.save(update_fields=["is_active","archived_at","booking_status","updated_at"])
        _invalidate_public_content_caches()
        from audit.logging_services import log_action
        log_action(request=self.request, action="hotel.archive", category="hotels", message=f"Hotel '{instance.name}' archived", object_type="Hotel", object_id=str(instance.id))

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def nearby(self, request):
        """Hotels within `radius_km` of the given coordinates, nearest first.

        Same contract family as /destinations/nearby/: latitude/longitude/
        radius_km query params (validated), haversine on stored coordinates,
        distance_km injected per row. No separate nearby dataset.
        """
        query_serializer = NearbyDestinationQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        lat = query_serializer.validated_data["latitude"]
        lon = query_serializer.validated_data["longitude"]
        radius_km = query_serializer.validated_data["radius_km"]

        try:
            page_size = max(1, min(int(request.query_params.get("page_size", 24)), 100))
        except (TypeError, ValueError):
            page_size = 24

        results = []
        box = bounding_box(lat, lon, radius_km)
        # Nearby reads only need coordinates and the selected page of hotel
        # records. Avoid the general list serializer's gallery prefetch and
        # constrain the scan with a bounding box before doing Python distance
        # calculations.
        queryset = self.get_queryset().prefetch_related(None).filter(
            latitude__gte=box["min_lat"], latitude__lte=box["max_lat"],
            longitude__gte=box["min_lon"], longitude__lte=box["max_lon"],
        )
        for hotel in queryset:
            distance = haversine_distance(lat, lon, hotel.latitude, hotel.longitude)
            if distance <= radius_km:
                results.append((distance, hotel))
        # Verified listings first, then nearest (label_unverified policy:
        # sourced unverified hotels are still shown, with a badge). Exact
        # duplicate imports (same name + coordinates) are listed once.
        from .views_ml import dedupe_service_rows
        results.sort(key=lambda pair: pair[0])
        results = dedupe_service_rows(results)
        results.sort(key=lambda pair: (not pair[1].is_verified, pair[0]))

        page = results[:page_size]
        data = self.get_serializer([h for _, h in page], many=True, context={"request": request}).data
        for row, (distance, _hotel) in zip(data, page):
            row["distance_km"] = round(float(distance), 2)
        return Response({"count": len(results), "results": data})


class RestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = RestaurantSerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "restaurants"
    filterset_fields = ["destination", "price_range", "vegetarian_friendly", "status", "is_verified"]
    search_fields = ["name", "cuisine_types", "address"]

    def get_queryset(self):
        queryset = Restaurant.objects.select_related("destination").order_by("-is_verified", "name", "id")
        user = self.request.user
        is_platform_admin = bool(user.is_authenticated and (user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}))
        if self.request.method in permissions.SAFE_METHODS and not is_platform_admin:
            queryset = queryset.filter(status="published")
        if user.is_authenticated and user.is_staff and not is_platform_admin:
            profile = StaffCapabilityProfile.objects.filter(user=user).first()
            districts = list(getattr(profile, "managed_districts", []) or [])
            if districts:
                scope = Q()
                for district in districts:
                    scope |= Q(destination__district__iexact=district) | Q(destination__city__iexact=district)
                queryset = queryset.filter(scope)
        return queryset

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user, status="pending", is_verified=False)

    def perform_update(self, serializer):
        if any(field in self.request.data for field in ("status", "is_verified")):
            from .views_admin import _require_capability
            _require_capability(self.request, "restaurants", "approve")
        before = {field: getattr(serializer.instance, field, None) for field in ("name", "address", "phone", "status", "is_verified")}
        restaurant = serializer.save(updated_by=self.request.user)
        _invalidate_public_content_caches()
        from audit.logging_services import log_action
        log_action(request=self.request, action="restaurant.update", category="restaurants", message=f"Restaurant '{restaurant.name}' updated", object_type="Restaurant", object_id=str(restaurant.id), extra={"before": before})

    def perform_destroy(self, instance):
        instance.status="archived";instance.updated_by=self.request.user;instance.save(update_fields=["status","updated_by","updated_at"])
        _invalidate_public_content_caches()
        from audit.logging_services import log_action
        log_action(request=self.request, action="restaurant.archive", category="restaurants", message=f"Restaurant '{instance.name}' archived", object_type="Restaurant", object_id=str(instance.id))


class TransitRouteViewSet(viewsets.ModelViewSet):
    serializer_class = DestinationTransitRouteSerializer
    permission_classes = [HasCapabilityOrReadOnly]
    capability_module = "transportation"
    filterset_fields = ["destination", "transport_mode", "is_active", "is_verified"]
    search_fields = ["origin", "transport_mode", "operator_name", "key_stops"]

    def get_queryset(self):
        queryset = DestinationTransitRoute.objects.select_related("destination")
        if self.request.method in permissions.SAFE_METHODS:
            queryset = queryset.filter(is_active=True, is_verified=True)
        user = self.request.user
        if user.is_authenticated and user.is_staff and not (user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}):
            from .views_admin import _scope_destination_queryset
            queryset = queryset.filter(destination_id__in=_scope_destination_queryset(Destination.objects.all(), user).values("id"))
        return queryset

    def perform_create(self, serializer): serializer.save(updated_by=self.request.user, is_verified=False)
    def perform_update(self, serializer):
        if any(field in self.request.data for field in ("is_active", "is_verified")):
            from .views_admin import _require_capability
            _require_capability(self.request, "transportation", "approve")
        serializer.save(updated_by=self.request.user)
    def perform_destroy(self, instance):
        instance.is_active=False;instance.updated_by=self.request.user;instance.save(update_fields=["is_active","updated_by","updated_at"])

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """Deliberate curation act: stamp the route as admin-verified with provenance.

        This is the ONLY sanctioned way to vouch for a manually recorded
        distance — it records who verified it and when (spec: manual values
        must be deliberate curated routes, never silent overrides).
        """
        from audit.logging_services import log_action
        from .views_admin import _require_capability, _require_destination_access
        _require_capability(request, "transportation", "approve")
        route = self.get_object()
        _require_destination_access(request, route.destination, "transportation", "approve")
        route.is_verified = True
        route.verified_at = timezone.now()
        route.confidence_level = "ADMIN_VERIFIED"
        route.updated_by = request.user
        route.save(update_fields=["is_verified", "verified_at", "confidence_level", "updated_by", "updated_at"])
        log_action(request=request, action="transit.verify", category="transportation",
                   message=f"Transit route '{route.origin} → {route.destination.name}' admin-verified",
                   object_type="DestinationTransitRoute", object_id=str(route.id))
        return Response(self.get_serializer(route).data)

    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        """Re-run the routing engine over the curated route's stored coordinates.

        Engine output lands as confidence CALCULATED and clears is_verified —
        a human must verify again. If the engine cannot route, the stored
        distance is kept untouched and the failure is reported honestly.
        """
        from audit.logging_services import log_action
        from .routing_service import route_metrics
        from .views_admin import _require_capability, _require_destination_access
        _require_capability(request, "transportation", "change")
        route = self.get_object()
        _require_destination_access(request, route.destination, "transportation", "change")
        if None in (route.origin_latitude, route.origin_longitude, route.destination_latitude, route.destination_longitude):
            return Response({"detail": "This route record has no stored coordinates — recalculation impossible. Add coordinates first; information unavailable until then."}, status=400)
        metrics = route_metrics(float(route.origin_latitude), float(route.origin_longitude),
                                float(route.destination_latitude), float(route.destination_longitude))
        if metrics.get("route_distance_km") is None:
            return Response({"detail": f"Routing engine could not produce a distance ({metrics.get('status')}). Stored value kept unchanged — information unavailable.",
                             "routing_status": metrics.get("status")}, status=503)
        before = {"distance_km": str(route.distance_km) if route.distance_km is not None else None,
                  "approx_duration": route.approx_duration, "confidence_level": route.confidence_level}
        route.distance_km = metrics["route_distance_km"]
        if metrics.get("duration_min"):
            mins = int(metrics["duration_min"])
            route.approx_duration = f"{mins // 60} hours {mins % 60} mins" if mins >= 60 else f"{mins} mins"
        route.confidence_level = "CALCULATED"
        route.is_verified = False
        route.updated_by = request.user
        route.save(update_fields=["distance_km", "approx_duration", "confidence_level", "is_verified", "updated_by", "updated_at"])
        log_action(request=request, action="transit.recalculate", category="transportation",
                   message=f"Transit route '{route.origin} → {route.destination.name}' recalculated: {before['distance_km']} → {route.distance_km} km ({metrics.get('status')})",
                   object_type="DestinationTransitRoute", object_id=str(route.id))
        return Response({"previous": before,
                         "current": {"distance_km": str(route.distance_km), "approx_duration": route.approx_duration,
                                     "confidence_level": route.confidence_level, "is_verified": route.is_verified},
                         "routing_status": metrics.get("status"), "note": metrics.get("note", ""),
                         "route": self.get_serializer(route).data})


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
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return queryset.none()
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

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return TravelPlanStop.objects.none()
        return TravelPlanStop.objects.filter(plan__user=self.request.user).select_related("destination", "transit_route")

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

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        is_platform = bool(user.is_authenticated and (user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}))
        if self.request.method in permissions.SAFE_METHODS and not is_platform:
            from .views_admin import _has_capability
            if not _has_capability(self.request, "safety", "approve"):
                queryset = queryset.filter(is_verified=True)
        return queryset

    def perform_create(self, serializer):
        if "is_verified" in self.request.data:
            from .views_admin import _require_capability
            _require_capability(self.request, "safety", "approve")
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        if "is_verified" in self.request.data:
            from .views_admin import _require_capability
            _require_capability(self.request, "safety", "approve")
        return super().perform_update(serializer)

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

    def get_queryset(self):
        queryset = super().get_queryset().exclude(phone_number__in=["", None])
        if self.request.method in permissions.SAFE_METHODS:
            from .views_admin import _has_capability
            if not _has_capability(self.request, "safety", "approve"):
                districts = list(getattr(getattr(self.request.user, "capability_profile", None), "managed_districts", []) or [])
                if districts:
                    queryset = queryset.filter(city__in=districts)
        return queryset

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
    serializer_class = None
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

    queryset = OSMEssentialService.objects.filter(is_archived=False)
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
    serializer_class = None
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
        if getattr(self, "swagger_fake_view", False) or not user.is_authenticated:
            return qs.none()
        if user.is_staff or user.role in {"admin", "super_admin", "tourism_admin", "content_moderator", "district_manager"}:
            profile = StaffCapabilityProfile.objects.filter(user=user).first()
            districts = list(getattr(profile, "managed_districts", []) or [])
            if getattr(user, "managed_district", "") and user.managed_district not in districts:
                districts.append(user.managed_district)
            if districts and not (user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}):
                qs = qs.filter(district__in=districts)
            return qs
        return qs.filter(submitted_by=user)

    def perform_create(self, serializer):
        serializer.save(status=InfrastructureSubmission.Status.PENDING, submitted_by=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.is_staff or self.request.user.role in {"admin", "super_admin", "tourism_admin", "content_moderator", "district_manager"}:
            from .views_admin import _require_capability
            _require_capability(self.request, "safety", "approve" if any(field in self.request.data for field in ("status", "reviewed_by", "reviewed_at", "published_object_id")) else "change")
        serializer.save()

    def perform_destroy(self, instance):
        if not (self.request.user.is_staff or self.request.user.role in {"admin", "super_admin", "tourism_admin"}):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff may delete a submission")
        from .views_admin import _require_capability
        _require_capability(self.request, "safety", "delete")
        instance.delete()

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
        profile = StaffCapabilityProfile.objects.filter(user=user).first()
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
        profile = StaffCapabilityProfile.objects.filter(user=user).first()
        if not (profile and profile.allows(self.capability_module, "change")):
            return False
        districts = list(getattr(profile, "managed_districts", []) or [])
        if getattr(user, "managed_district", "") and user.managed_district not in districts:
            districts.append(user.managed_district)
        destination = getattr(instance, "destination", None)
        return not districts or (destination is not None and str(getattr(destination, "district", "") or "").casefold() in {d.casefold() for d in districts})

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
    def _name_index(prefix=""):
        """Return a bounded, prefix-scoped name index for typo suggestions.

        Building an index of every destination on the first arbitrary query
        made autocomplete unnecessarily slow on a cold process. Candidate
        lookup is now limited to names that share the first two characters,
        and the result is capped so a broad query cannot scan the catalogue.
        """
        from functools import lru_cache

        @lru_cache(maxsize=32)
        def build(prefix_key):
            qs = Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED,
            ).select_related("category")
            if prefix_key:
                qs = qs.filter(
                    Q(name__istartswith=prefix_key) | Q(name__icontains=prefix_key)
                )
            return [
                (d.name.lower(), d.name, d.slug, d.category.slug if d.category_id else "")
                for d in qs.order_by("name")[:500]
            ]
        return build((prefix or "").strip().lower()[:2])

    def _autocorrect(self, q, results):
        """Fuzzy 'did you mean' correction against real destination names."""
        import difflib

        from .filters import ACCOMMODATION_SLUGS
        norm = q.strip().lower()
        index = self._name_index(norm[:2])

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
    serializer_class = None
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
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            latitude = float(request.query_params.get("latitude") or request.query_params.get("lat"))
            longitude = float(request.query_params.get("longitude") or request.query_params.get("lng"))
            # Floor of 0.1 km, not 1 km: the radius picker offers 500 m, and
            # the old clamp silently widened every sub-kilometre emergency
            # search to a full kilometre (returning places the user excluded).
            radius_km = max(0.1, min(float(request.query_params.get("radius_km", 50)), 300))
            limit = max(1, min(int(request.query_params.get("limit", 8)), 25))
        except (KeyError, TypeError, ValueError):
            return Response(
                {"detail": "Valid latitude and longitude query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .emergency_service import build_emergency_directory
        try:
            payload = build_emergency_directory(latitude, longitude, radius_km=radius_km, limit=limit)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payload)


class NationalEmergencyHotlinesView(APIView):
    """Return the verified national emergency contacts without requiring GPS."""
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .emergency_service import national_hotlines
        return Response({"national_hotlines": national_hotlines(), "source": "Admin-managed records with required Nepal emergency fallbacks"})


def _hours_rows(rows, open_only=False):
    """Attach open-now status to OSM POI rows; optionally keep only open ones."""
    from .opening_hours import annotate
    rows = annotate(rows)
    return [r for r in rows if r["hours"]["state"] == "open"] if open_only else rows


class NearbyPOIsView(APIView):
    """Coordinate-first nearby places (master spec §2): USER location → real places.

    Accepts any coordinates (device GPS, manually chosen place, itinerary
    stop) — never limited to the destination database. Merges OpenStreetMap
    results with verified database destinations so admin-added places appear
    too (spec §9). Falls back honestly when the live provider is down (§60).
    """
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .opening_hours import truthy
        open_only = truthy(request.query_params.get("open_now"))
        from django.core.cache import cache
        from .services.overpass import search_pois

        try:
            lat = float(request.query_params.get("latitude"))
            lon = float(request.query_params.get("longitude"))
        except (TypeError, ValueError):
            return Response({"detail": "latitude and longitude are required — your current location or a chosen place."}, status=400)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return Response({"detail": "Coordinates are outside the valid range."}, status=400)
        try:
            radius_km = max(0.5, min(float(request.query_params.get("radius_km", 5)), 25))
        except (TypeError, ValueError):
            radius_km = 5.0
        cats = [c.strip() for c in str(request.query_params.get("categories", "")).split(",") if c.strip()] or None

        from .models import SiteSetting
        config_version = ""
        setting = SiteSetting.objects.filter(key="poi_categories").first()
        if setting:
            config_version = str(setting.updated_at.timestamp())
        cache_key = f"osm-pois-c:{round(lat, 3)}:{round(lon, 3)}:{radius_km}:{','.join(cats or [])}:{config_version}"
        cached = cache.get(cache_key)
        if cached is not None:
            groups, meta, error = cached["groups"], cached["meta"], cached["error"]
        else:
            groups, meta, error = search_pois(lat, lon, radius_km * 1000, cats)
            # Cache ONLY the external OSM results. Admin-managed DB places are
            # merged fresh below so CMS edits/archives are immediate.
            cache.set(cache_key, {"groups": groups, "meta": meta, "error": error}, 900)
        meta_by_key = {item["key"]: item for item in meta}

        # Verified database places (spec §9): admin-managed destinations near
        # the search point, merged into results with clear provenance.
        box = bounding_box(lat, lon, radius_km)
        db_rows = []
        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
            latitude__gte=box["min_lat"], latitude__lte=box["max_lat"],
            longitude__gte=box["min_lon"], longitude__lte=box["max_lon"],
        )[:60]
        for dest in qs:
            distance = haversine_distance(lat, lon, dest.latitude, dest.longitude)
            if distance <= radius_km:
                # A distance is only as precise as the pin it points at. A
                # destination recorded to two decimals is a town centre good to
                # about a kilometre, so publishing "0.34 km" without the
                # uncertainty would state more precision than the data has.
                from .coordinate_accuracy import classify_precision, resolution_km

                db_rows.append({
                    "name": dest.name,
                    "latitude": float(dest.latitude),
                    "longitude": float(dest.longitude),
                    "distance_km": round(distance, 2),
                    "coordinate_accuracy": dest.coordinate_accuracy
                    or classify_precision(dest.latitude, dest.longitude),
                    "distance_uncertainty_km": resolution_km(dest.latitude, dest.longitude),
                    "slug": dest.slug,
                    "source": "Tourism database (approved listing)",
                    "source_url": f"/destinations/{dest.slug}",
                })
        db_rows.sort(key=lambda row: row["distance_km"])

        payload = {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius_km,
            "distance_note": "Straight-line distances from the search point.",
            "categories": {
                key: {
                    "label": meta_by_key.get(key, {}).get("label", key),
                    "icon": meta_by_key.get(key, {}).get("icon", ""),
                    "results": _hours_rows(groups.get(key, []), open_only),
                }
                for key in groups
            },
            "open_now_filter": open_only,
            "hours_note": "Open/closed is worked out from OpenStreetMap opening hours in Nepal time. Places without hours are never shown as open.",
            "verified_database_places": db_rows[:15],
            "provider_error": error,
        }
        return Response(payload)


class DestinationNearbyPOIsView(APIView):
    """Real nearby places around a destination from OpenStreetMap (Overpass).

    Location-based, NOT limited to our own Destination table: hotels,
    hospitals, temples, viewpoints, restaurants, banks, ATMs, peaks, police
    and pharmacies within radius_km, nearest first, each with straight-line
    distance_km. Results are cached per rounded location so hot pages never
    hammer the free Overpass API. Provenance is always disclosed.
    """
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    CATEGORIES = {
        "hotels": ('node["tourism"~"^(hotel|guest_house|hostel)$"]', "Hotels & lodges"),
        "hospitals": ('node["amenity"~"^(hospital|clinic)$"]', "Hospitals & clinics"),
        "temples": ('node["amenity"="place_of_worship"]', "Temples & shrines"),
        "viewpoints": ('node["tourism"="viewpoint"]', "Viewpoints"),
        "restaurants": ('node["amenity"~"^(restaurant|cafe)$"]', "Restaurants & cafés"),
        "banks": ('node["amenity"~"^(bank|bureau_de_change)$"]', "Banks & exchange"),
        "atms": ('node["amenity"="atm"]', "ATMs"),
        "peaks": ('node["natural"="peak"]', "Peaks & hills"),
        "police": ('node["amenity"="police"]', "Police"),
        "pharmacies": ('node["amenity"="pharmacy"]', "Pharmacies"),
    }
    DEFAULT_CATEGORIES = ["hotels", "hospitals", "police", "temples", "viewpoints", "restaurants", "banks"]

    @staticmethod
    def _categorize(tags):
        tourism = tags.get("tourism", "")
        amenity = tags.get("amenity", "")
        natural = tags.get("natural", "")
        if tourism in {"hotel", "guest_house", "hostel"}:
            return "hotels"
        if amenity in {"hospital", "clinic"}:
            return "hospitals"
        if amenity == "place_of_worship":
            return "temples"
        if tourism == "viewpoint":
            return "viewpoints"
        if amenity in {"restaurant", "cafe"}:
            return "restaurants"
        if amenity in {"bank", "bureau_de_change"}:
            return "banks"
        if amenity == "atm":
            return "atms"
        if natural == "peak":
            return "peaks"
        if amenity == "police":
            return "police"
        if amenity == "pharmacy":
            return "pharmacies"
        return None

    @classmethod
    def _database_fallback(cls, lat, lon, radius_km, wanted):
        """Honest offline fallback from admin-managed database tables.

        Hospitals/police come from the curated service directories, stays
        from name-matched approved destinations, category groups from
        categorized destinations, and banks/ATMs/pharmacies from the
        OSM-sourced essential-service directories (real imported
        coordinates — never fabricated).

        The directories are sparsely populated (a few hundred records for
        the whole country), so a strict small-radius box returns empty for
        most districts. Instead we EXPAND the search radius in steps until
        each category finds records, and report the effective search radius
        so the UI can say "nearest hospital 23 km away" rather than
        pretending nothing exists. A category with no records even at the
        maximum radius comes back empty with an explicit note."""
        from .models import Destination, Hospital, OSMEssentialService, PoliceStation, Hotel, Restaurant

        # Step radii: requested -> x2 -> x4 ... up to 150 km. Sparse
        # national directories need the wider steps; the distance_km on
        # every row stays truthful either way.
        radii = []
        r = max(1.0, float(radius_km))
        while r <= 150.0:
            radii.append(r)
            r *= 2
        if radii[-1] < 150.0:
            radii.append(150.0)

        # Load each candidate set ONCE (no bounding-box pre-filter — the
        # tables are small: <6k rows total) and distance-rank in Python so
        # tier expansion never re-queries.
        # These rows are assembled straight from model attributes rather than
        # through a serializer, so they need the publish-safe phone helper
        # themselves: migration 0086 cleaned what is stored, but an import or
        # an admin edit after that must not be able to serve "nan" as a number.
        from .phone_quality import usable_phone

        hospital_rows = [
            (h.name, float(h.latitude), float(h.longitude), {"phone": usable_phone(h.phone)})
            for h in Hospital.objects.filter(is_archived=False)
            if h.latitude is not None and h.longitude is not None
        ]
        police_rows = [
            (p.name, float(p.latitude), float(p.longitude), {"phone": usable_phone(p.phone)})
            for p in PoliceStation.objects.filter(is_archived=False)
            if p.latitude is not None and p.longitude is not None
        ]
        dest_qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED
        )
        stay_q = Q()
        for word in ("hotel", "lodge", "resort", "guest house", "guesthouse",
                     "homestay", "inn"):
            stay_q |= Q(name__icontains=word)
        hotel_rows = [
            (h.name, float(h.latitude), float(h.longitude), {"phone": usable_phone(h.phone), "address": h.address, "price": str(h.price_per_night) if h.price_per_night else None})
            for h in Hotel.objects.filter(is_active=True).exclude(latitude=None).exclude(longitude=None)
        ] + [
            (d.name, float(d.latitude), float(d.longitude), {"slug": d.slug})
            for d in dest_qs.filter(stay_q).exclude(latitude=None).exclude(longitude=None)
        ]
        restaurant_rows = [
            (r.name, float(r.latitude), float(r.longitude), {"phone": usable_phone(r.phone), "address": r.address, "cuisine": r.cuisine_types})
            for r in Restaurant.objects.filter(status="published").exclude(latitude=None).exclude(longitude=None)
        ] + [
            (d.name, float(d.latitude), float(d.longitude), {"slug": d.slug})
            for d in dest_qs.filter(category__slug__in=["food-culinary"]).exclude(latitude=None).exclude(longitude=None)
        ]
        category_slugs = {"temples": ["temples"], "viewpoints": ["viewpoints"],
                          "restaurants": ["food-culinary"],
                          "peaks": ["mountains", "hills"]}
        category_rows = {}
        for key, slugs in category_slugs.items():
            category_rows[key] = [
                (d.name, float(d.latitude), float(d.longitude), {"slug": d.slug})
                for d in dest_qs.filter(category__slug__in=slugs)
                if d.latitude is not None and d.longitude is not None
            ]
        service_categories = {
            "banks": (["bank"], "Tourism database — bank directory (OSM-sourced)"),
            "atms": (["atm"], "Tourism database — ATM directory (OSM-sourced)"),
            "pharmacies": (["pharmacy"],
                           "Tourism database — pharmacy directory (OSM-sourced)"),
        }
        service_rows = {
            key: [
                (s.name, float(s.latitude), float(s.longitude),
                 {"phone": s.phone or None, "address": s.address or None})
                for s in OSMEssentialService.objects.filter(
                    category__in=cats, is_archived=False
                ).exclude(name__icontains="name not recorded")
                if s.latitude is not None and s.longitude is not None
            ]
            for key, (cats, _label) in service_categories.items()
        }

        source_for = {
            "hospitals": "Tourism database — hospital directory",
            "police": "Tourism database — police directory",
            "hotels": "Tourism database — likely stays (name-matched)",
            "temples": "Tourism database — admin-verified destinations",
            "viewpoints": "Tourism database — admin-verified destinations",
            "restaurants": "Tourism database — admin-verified destinations",
            "peaks": "Tourism database — admin-verified destinations",
        }

        def candidate_pool(key):
            if key == "hospitals":
                return hospital_rows
            if key == "police":
                return police_rows
            if key == "hotels":
                return hotel_rows
            if key == "restaurants":
                return restaurant_rows
            if key in category_rows:
                return category_rows[key]
            if key in service_rows:
                return service_rows[key]
            return []

        def search(key):
            """Nearest-first results with tiered radius expansion."""
            pool = candidate_pool(key)
            if not pool:
                return [], radii[-1]
            # Directory rows imported from district lists carry a town-centre point
            # rather than the building's coordinates (28 Biratnagar hospitals share
            # ONE point, and coordinate_source/status are blank on every row).
            # Three or more rows on the same 4-decimal point is that signature, so
            # their distance is only good to a few km and is labelled as an area
            # point instead of a metre-precise figure.
            from collections import Counter
            shared_points = Counter((round(r[1], 4), round(r[2], 4)) for r in pool)
            for radius in radii:
                found = []
                for name, rlat, rlon, extra in pool:
                    d = haversine_distance(lat, lon, rlat, rlon)
                    if d is not None and d <= radius:
                        is_approx = bool(
                            extra.get("is_approximate")
                            or (round(rlat, 4) == round(lat, 4) and round(rlon, 4) == round(lon, 4))
                            or shared_points[(round(rlat, 4), round(rlon, 4))] >= 3
                        )
                        dist_label = f"≈ {round(d, 2)} km (area point)" if is_approx else f"{round(d, 2)} km"
                        row_item = {
                            "name": name,
                            "distance_km": round(d, 2),
                            "distance_label": dist_label,
                            "is_approximate": is_approx,
                            "latitude": rlat,
                            "longitude": rlon,
                            "source": source_for.get(key, service_categories.get(key, ("", "Tourism database"))[1]),
                        }
                        if extra:
                            row_item.update(extra)
                        row_item["is_approximate"] = is_approx
                        row_item["distance_label"] = dist_label
                        found.append(row_item)
                if found:
                    found.sort(key=lambda row: (row.get("is_approximate", False), row["distance_km"]))
                    # Collapse same-site duplicates: the same facility is
                    # often recorded twice under slightly different names at
                    # identical coordinates (88 hospital / 222 police pairs
                    # in the current directories). Keep the nearest entry.
                    seen_sites = set()
                    unique = []
                    for row in found:
                        site = (round(row["latitude"], 3), round(row["longitude"], 3))
                        if site in seen_sites:
                            continue
                        seen_sites.add(site)
                        unique.append(row)
                    return unique[:10], radius
            return [], radii[-1]

        categories = {}
        for key in wanted:
            data, searched_radius = search(key)
            entry = {"label": cls.CATEGORIES[key][1], "results": data,
                     "searched_radius_km": round(searched_radius, 1)}
            if not data:
                entry["note"] = (f"No offline records within {round(searched_radius)} km — "
                                 "live OpenStreetMap data is required for this category here.")
            categories[key] = entry

        return {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius_km,
            "distance_note": "Straight-line distances from the destination coordinates.",
            "source": "Tourism database (offline fallback — live map data unavailable)",
            "provider_error": ("Live OpenStreetMap (Overpass) lookup failed; "
                               "showing admin-managed database places instead."),
            "categories": categories,
        }

    HOURS_NOTE = ("Open/closed is worked out from OpenStreetMap opening hours in Nepal time. "
                  "Places without hours are never shown as open.")

    def get(self, request, destination_ref):
        from .opening_hours import truthy
        response = self._get(request, destination_ref)
        data = getattr(response, "data", None)
        if response.status_code == 200 and isinstance(data, dict) and isinstance(data.get("categories"), dict):
            open_only = truthy(request.query_params.get("open_now"))
            out = dict(data)  # never mutate the cached payload
            out["categories"] = {
                key: {**entry, "results": _hours_rows([dict(r) for r in entry.get("results") or []], open_only)}
                for key, entry in data["categories"].items()
            }
            out["open_now_filter"] = open_only
            out["hours_note"] = self.HOURS_NOTE
            response.data = out
        return response

    def _get(self, request, destination_ref):
        import requests as http_requests
        from django.core.cache import cache
        from .emergency_service import resolve_destination

        destination = resolve_destination(destination_ref)
        if destination is None:
            return Response({"detail": "Approved destination not found."}, status=status.HTTP_404_NOT_FOUND)
        lat, lon = destination.latitude, destination.longitude
        if lat is None or lon is None:
            return Response({"detail": "This destination has no recorded coordinates, so a live nearby lookup is impossible."}, status=422)
        try:
            radius_km = max(1.0, min(float(request.query_params.get("radius_km", 5)), 25))
        except (TypeError, ValueError):
            radius_km = 5.0
        wanted = [c.strip() for c in str(request.query_params.get("categories", "")).split(",") if c.strip() in self.CATEGORIES]
        if not wanted:
            wanted = list(self.DEFAULT_CATEGORIES)
        radius_m = int(radius_km * 1000)

        cache_key = f"osm-pois:{round(float(lat), 3)}:{round(float(lon), 3)}:{radius_m}:{','.join(wanted)}"
        cached = cache.get(cache_key)
        if cached is not None:
            # Destination name is admin-managed: merge fresh, never from cache.
            return Response({**cached, "destination": destination.name})

        parts = "".join(f"{self.CATEGORIES[key][0]}(around:{radius_m},{lat},{lon});" for key in wanted)
        query = f"[out:json][timeout:15];({parts});out body 300;"
        # Mirror failover across public Overpass endpoints before falling back.
        from .services.overpass import overpass_post
        elements, upstream_error = overpass_post(query, timeout=18)
        if upstream_error is not None:
            # Never a dead end: serve admin-managed database places instead
            # (hospitals, police, stays, category-matched destinations) with
            # clear provenance, so "nearby hospital/hotel" always answers.
            # Cache the fallback too (short TTL) — otherwise every repeat
            # visit re-pays the full 18 s Overpass failover when the
            # network/OSM is unreachable, which made pages feel "very slow".
            payload = self._database_fallback(float(lat), float(lon), radius_km, wanted)
            try:
                cache.set(cache_key, payload, 300)
            except Exception:  # pragma: no cover — cache backend failures
                pass
            return Response({**payload, "destination": destination.name})

        grouped = {key: [] for key in wanted}
        for element in elements:
            tags = element.get("tags") or {}
            name = tags.get("name") or tags.get("name:en") or tags.get("operator")
            key = self._categorize(tags)
            if not name or key not in grouped:
                continue
            distance = haversine_distance(lat, lon, element.get("lat"), element.get("lon"))
            grouped[key].append({
                "name": name,
                "distance_km": round(distance, 2),
                "latitude": element.get("lat"),
                "longitude": element.get("lon"),
                "osm_id": element.get("id"),
                "source": "OpenStreetMap (Overpass API)",
            })
        categories = {}
        for key in wanted:
            rows = sorted(grouped[key], key=lambda row: row["distance_km"])[:10]
            categories[key] = {"label": self.CATEGORIES[key][1], "results": rows}
        # OSM amenity nodes are sparse in rural Nepal (a whole district may
        # have zero hospital/bank nodes) while the admin-managed directories
        # have nationwide coverage. When live OSM is empty for a category,
        # supplement from those directories — per-row provenance stays
        # truthful, and a category that exists nowhere stays honestly empty.
        supplemented = [key for key in wanted if not categories[key]["results"]]
        if supplemented:
            fallback = self._database_fallback(float(lat), float(lon), radius_km, supplemented)
            for key in supplemented:
                fb_entry = fallback["categories"][key]
                if fb_entry.get("results"):
                    fb_entry["note"] = ("Live map data has no records here; showing "
                                        "admin-managed database places instead.")
                categories[key] = fb_entry
            payload_source = ("OpenStreetMap (Overpass API), empty categories "
                              "supplemented from the Tourism database")
        else:
            payload_source = "OpenStreetMap (Overpass API)"
        payload = {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius_km,
            "distance_note": "Straight-line distances from the destination coordinates.",
            "source": payload_source,
            "categories": categories,
        }
        # Cache the external OSM payload only; the admin-managed destination
        # name is merged fresh on every response (hit or miss).
        cache.set(cache_key, payload, 900)
        return Response({**payload, "destination": destination.name})


class DestinationEmergencyServicesView(APIView):
    """Nearest services plus destination risk for any approved Nepal place."""
    serializer_class = None

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
    serializer_class = None
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


class DistrictsListView(APIView):
    """All 77 canonical districts with REAL coverage numbers (§15).

    Counts come straight from the database; districts without verified
    data are reported honestly as no_verified_data — never padded.
    """
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.db.models import Count

        from .management.commands.normalize_district_names import (
            NEPAL_DISTRICTS as PROVINCE_DISTRICTS)
        from .administrative_boundaries import NEPAL_DISTRICTS_DATA

        district_index = {}
        for province, names in PROVINCE_DISTRICTS.items():
            for name in names:
                district_index[name] = {
                    "province": province,
                    **(NEPAL_DISTRICTS_DATA.get(name) or {})}

        counts = {
            r["district"]: r["n"]
            for r in Destination.objects.filter(
                status=Destination.SubmissionStatus.APPROVED, is_active=True)
            .exclude(district="").exclude(district=None)
            .values("district").annotate(n=Count("id"))
        }
        rows = []
        for name, meta in sorted(district_index.items()):
            n = counts.get(name, 0)
            rows.append({
                "name": name,
                "province": meta["province"],
                "latitude": meta.get("lat"),
                "longitude": meta.get("lng"),
                "public_destinations": n,
                "coverage_status": (
                    "well_covered" if n >= 20 else
                    "partially_covered" if n >= 5 else
                    "limited_data" if n >= 1 else "no_verified_data"),
            })
        provinces = {}
        for row in rows:
            provinces.setdefault(row["province"], 0)
            provinces[row["province"]] += row["public_destinations"]
        return Response({
            "count": len(rows),
            "provinces": provinces,
            "note": ("Coverage reflects verified database records only; "
                     "districts are never artificially populated."),
            "districts": rows,
        })


def _unique_places(rows):
    """Directory rows as dicts, skipping exact repeats (same name, point and
    phone). The imported directory has a few duplicated records; listing the
    same station twice helps nobody, and the source data stays untouched."""
    seen, out = set(), []
    for row in rows:
        item = {"id": row.pk, "name": row.name, "phone": usable_phone(row.phone),
                "latitude": float(row.latitude), "longitude": float(row.longitude)}
        key = (row.name.strip().lower(), item["latitude"], item["longitude"], item["phone"])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


class DistrictDetailView(APIView):
    """Database-generated district page data (§16-17)."""
    serializer_class = None

    permission_classes = [permissions.AllowAny]

    def get(self, request, district_name):
        from django.db.models import Count

        from .management.commands.normalize_district_names import (
            NEPAL_DISTRICTS as PROVINCE_DISTRICTS)
        from .administrative_boundaries import NEPAL_DISTRICTS_DATA
        from .models import Hospital, PoliceStation

        all_districts = [n for names in PROVINCE_DISTRICTS.values() for n in names]
        # match canonical name case-insensitively
        match = next((k for k in all_districts
                      if k.lower() == district_name.strip().lower()), None)
        if match is None:
            return Response({"detail": f"{district_name} is not one of Nepal's "
                                       "77 canonical districts."},
                            status=status.HTTP_404_NOT_FOUND)
        meta = {"province": next(p for p, ns in PROVINCE_DISTRICTS.items()
                                 if match in ns),
                **(NEPAL_DISTRICTS_DATA.get(match) or {})}
        pub = Destination.objects.filter(
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
            district=match)
        cities = [
            {"name": r["city"], "destinations": r["n"]}
            for r in pub.exclude(city="").exclude(city=None)
            .values("city").annotate(n=Count("id")).order_by("-n")
        ]
        categories = [
            {"name": r["category__name"], "destinations": r["n"]}
            for r in pub.exclude(category=None)
            .values("category__name").annotate(n=Count("id")).order_by("-n")
        ]
        top = pub.order_by("-average_rating", "-ratings_count", "name")[:10]
        hospitals = Hospital.objects.filter(
            destination__district=match).select_related("destination")[:20]
        police = PoliceStation.objects.filter(
            destination__district=match).select_related("destination")[:20]
        return Response({
            "district": match,
            "province": meta["province"],
            "latitude": meta.get("lat"),
            "longitude": meta.get("lng"),
            "public_destinations": pub.count(),
            "cities": cities,
            "categories": categories,
            "top_destinations": [
                {"name": d.name, "slug": d.slug,
                 "latitude": float(d.latitude) if d.latitude else None,
                 "longitude": float(d.longitude) if d.longitude else None,
                 "category": d.category.name if d.category else None,
                 "average_rating": float(d.average_rating) if d.average_rating else None,
                 "short_description": d.short_description}
                for d in top
            ],
            "hospitals": _unique_places(hospitals),
            "police": _unique_places(police),
            "note": ("" if pub.exists() else
                     "No verified destinations recorded for this district "
                     "yet — nothing is fabricated to fill the gap."),
        })


class DistrictGalleryView(APIView):
    """Up to five destination-linked media items per represented Nepal district."""
    serializer_class = None
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
                url = public_media_url(photo.image.url, request)
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
    serializer_class = None

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
        payload = build_destination_risk(destination)
        # Attach the structured, admin-curated risk profile (causes,
        # accident history, travel safety, weather, emergency coverage)
        # so travellers see the reviewed factors behind the score.
        risk = getattr(destination, "risk_analysis", None)
        if risk is not None:
            from .serializers import RiskProfileSerializer
            payload["risk_profile"] = RiskProfileSerializer(risk).data
        return Response(payload)


class RiskProfileAdminView(APIView):
    """Admin read/update of a destination's curated risk profile.

    Lets staff with the safety.change capability assign and review
    the structured risk factors — accident history, travel safety,
    weather exposure, emergency coverage and risk causes — for any
    approved destination, resolved by slug/id/name. Updates stamp
    ``last_reviewed`` and ``reviewed_by`` so the review trail is
    visible to travellers.
    """
    serializer_class = None
    permission_classes = [HasCapability]
    capability_module = "safety"

    # Curated, admin-editable risk factors.
    CURATED_FIELDS = [
        # accident history
        "accidents", "accidents_last_year", "fatal_accidents_last_year",
        "accidents_last_5y", "accident_trend", "last_major_incident_date",
        # hazard counts
        "landslide", "avalanche", "flood", "earthquake_damage",
        # travel safety
        "travel_safety_score", "travel_safety_rating",
        "solo_travel_safety", "night_safety", "family_safety",
        "female_traveler_safety", "road_quality", "trail_marking",
        "mobile_network_coverage",
        # weather exposure
        "monsoon_risk", "winter_snow_risk", "summer_heat_risk",
        "lightning_risk", "high_altitude_risk", "uv_exposure",
        # emergency & life safety
        "hospital_count", "police_count", "fire_station_count",
        "hospital_coverage", "emergency_response_minutes",
        "rescue_availability", "medical_facility_level", "police_presence",
        # causes & overall
        "risk_causes", "overall_safety_score", "safety_summary",
        "emergency_risk", "natural_disaster_risk", "tourism_risk_index",
        "risk_category",
    ]

    def _resolve(self, destination_ref):
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
        return destination

    def get(self, request, destination_ref):
        destination = self._resolve(destination_ref)
        if destination is None:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)
        risk = getattr(destination, "risk_analysis", None)
        if risk is None:
            return Response({"detail": "No risk profile recorded for this destination yet."},
                            status=status.HTTP_404_NOT_FOUND)
        from .serializers import RiskProfileSerializer
        return Response(RiskProfileSerializer(risk).data)

    def patch(self, request, destination_ref):
        destination = self._resolve(destination_ref)
        if destination is None:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)
        payload = request.data if isinstance(request.data, dict) else {}
        risk = getattr(destination, "risk_analysis", None)
        if risk is None:
            from .models import RiskAnalysis
            risk = RiskAnalysis.objects.create(
                destination=destination,
                emergency_risk=float(payload.get("emergency_risk", 50) or 50),
                natural_disaster_risk=float(payload.get("natural_disaster_risk", 50) or 50),
                tourism_risk_index=float(payload.get("tourism_risk_index", 50) or 50),
                risk_category=str(payload.get("risk_category", "moderate") or "moderate"),
            )

        updates = {}
        for field in self.CURATED_FIELDS:
            if field in payload:
                value = payload[field]
                # Normalize empty strings to None for nullable fields.
                if value == "" and field in {
                    "travel_safety_score", "overall_safety_score",
                    "emergency_response_minutes", "last_major_incident_date",
                    "safety_summary",
                }:
                    value = None
                updates[field] = value

        if not updates:
            return Response({"detail": "No recognised risk fields to update."},
                            status=status.HTTP_400_BAD_REQUEST)

        for field, value in updates.items():
            setattr(risk, field, value)
        risk.last_reviewed = timezone.now()
        risk.reviewed_by = request.user
        risk.save(update_fields=list(updates.keys()) + ["last_reviewed", "reviewed_by", "updated_at"])

        from .serializers import RiskProfileSerializer
        from audit.models import AuditLog
        AuditLog.objects.create(
            user=request.user, user_email=request.user.email,
            actor_role=getattr(request.user, "role", ""),
            category="safety", severity="info", source="backend",
            action="risk.profile.update",
            message=f"Updated curated risk profile for {destination.name}",
            object_type="RiskAnalysis", object_id=str(risk.id),
            extra={"destination": destination.name, "fields": list(updates.keys())},
        )
        return Response(RiskProfileSerializer(risk).data)


NEPAL_HIGHWAYS = {
    "kaski": "H04 Prithvi Highway & H05 Siddhartha Highway",
    "pokhara": "H04 Prithvi Highway & H05 Siddhartha Highway",
    "kathmandu": "H02 Tribhuvan Highway & Ring Road (H16)",
    "lalitpur": "H02 Tribhuvan Highway & Ring Road (H16)",
    "bhaktapur": "H03 Arniko Highway",
    "chitwan": "H01 Mahendra Highway & H04 Prithvi Highway",
    "solukhumbu": "H15 Pasang Lhamu Highway & Lukla Air Corridor",
    "mustang": "H18 Kali Gandaki Corridor & Jomsom Highway",
    "manang": "H18 Kali Gandaki & Annapurna Circuit Trail",
    "ilam": "H07 Mechi Highway",
    "sunsari": "H08 Koshi Highway",
    "morang": "H01 Mahendra Highway & H08 Koshi Highway",
    "dhanusha": "H10 Postal Highway & H01 Mahendra Highway",
    "rupandehi": "H01 Mahendra Highway & H05 Siddhartha Highway",
    "palpa": "H05 Siddhartha Highway",
    "tanahun": "H04 Prithvi Highway",
    "syangja": "H05 Siddhartha Highway",
    "myagdi": "H18 Kali Gandaki Corridor",
    "gorkha": "H04 Prithvi Highway & Benighat Corridor",
    "mugu": "H06 Karnali Highway & Talcha Corridor",
    "dolpa": "H06 Karnali Highway & Dunai Trail",
    "jumla": "H06 Karnali Highway",
    "surkhet": "H06 Karnali Highway & Ratna Highway (H12)",
    "kailali": "H01 Mahendra Highway",
    "kanchanpur": "H01 Mahendra Highway & Mahakali Corridor",
    "doti": "H14 Bhimdatta Highway",
    "darchula": "H14 Bhimdatta Highway & Mahakali Corridor",
    "sankhuwasabha": "H08 Koshi Highway Corridor",
    "taplejung": "H07 Mechi Highway Corridor",
}


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
    queryset = Destination.objects.none()

    # Mood -> category slugs + keywords (the model's learned weight table).
    # Every slug below must exist as a Category.slug in the live database: a
    # slug with no category is a silently dead signal, so the 0.45 category
    # weight never fires for that mood. "hill-stations", "national-park",
    # "nature" and "parks-gardens" were all dead, and "nature" was defined
    # twice so the second definition silently won.
    MOOD_PROFILES = {
        "relaxed":   {"cats": ["lakes", "lakes-water-bodies", "hot-springs", "spiritual-wellness", "hills", "hill-stations-and-views"], "kw": ["lake", "peace", "garden", "spa", "phewa", "begnas"]},
        "relax":     {"cats": ["lakes", "hot-springs", "spiritual-wellness"], "kw": ["lake", "peace", "garden"]},
        "chill":     {"cats": ["lakes", "cities", "hills", "hill-stations-and-views"], "kw": ["lakeside", "pokhara", "cafe", "thamel", "phewa"]},
        "adventure": {"cats": ["trekking", "trekking-nature", "adventure", "adventure-and-mountain", "air-sports", "water-sports", "mountains"], "kw": ["trek", "rafting", "bungee", "paragliding", "peak", "base camp", "canyon"]},
        "adventurous": {"cats": ["trekking", "trekking-nature", "adventure", "adventure-and-mountain", "air-sports", "water-sports", "mountains"], "kw": ["trek", "climb", "peak", "expedition"]},
        "romantic":  {"cats": ["lakes", "viewpoints", "viewpoints-hillstations", "hills", "villages"], "kw": ["sunrise", "lake", "hill", "pagoda", "phewa", "sarangkot", "nagarkot"]},
        "family":    {"cats": ["wildlife", "wildlife-and-nature", "cities", "museums", "forests", "viewpoints", "heritage"], "kw": ["national park", "safari", "museum", "chitwan", "cable car", "zoo", "family", "park"]},
        "spiritual": {"cats": ["pilgrimage", "pilgrimage-and-sacred", "religious-pilgrimage", "temples", "buddhist-sites", "spiritual-wellness"], "kw": ["temple", "stupa", "monastery", "gompa", "pilgrim", "pashupati", "lumbini", "muktinath", "manakamana", "pathibhara"]},
        "religious": {"cats": ["pilgrimage", "religious-pilgrimage", "temples", "buddhist-sites"], "kw": ["temple", "stupa", "dham", "mandir"]},
        "peaceful":  {"cats": ["lakes", "spiritual-wellness", "hills"], "kw": ["lake", "gompa", "monastery", "village", "retreat"]},
        "cultural":  {"cats": ["heritage", "heritage-culture", "culture", "museums", "festivals", "cities"], "kw": ["durbar", "palace", "heritage", "newar", "traditional", "museum", "bazaar"]},
        "culture":   {"cats": ["heritage", "heritage-culture", "culture", "museums"], "kw": ["durbar", "palace", "heritage"]},
        "heritage":  {"cats": ["heritage", "heritage-culture", "museums", "cities"], "kw": ["durbar", "palace", "fort", "gadhi", "heritage", "museum", "unesco"]},
        "wildlife":  {"cats": ["wildlife", "wildlife-and-nature", "bird-watching", "forests"], "kw": ["national park", "safari", "rhino", "tiger", "elephant", "bird", "reserve"]},
        "jungle":    {"cats": ["wildlife", "forests"], "kw": ["jungle", "safari", "chitwan", "bardiya"]},
        "trekking":  {"cats": ["trekking", "trekking-nature", "mountains", "valleys"], "kw": ["trek", "base camp", "circuit", "himal", "pass", "peak"]},
        "hiking":    {"cats": ["trekking", "trekking-nature", "viewpoints", "hills"], "kw": ["hill", "viewpoint", "hike", "poon hill"]},
        "scenic":    {"cats": ["viewpoints", "viewpoints-hillstations", "natural-wonders", "mountains", "lakes"], "kw": ["view", "sunrise", "panorama", "himal", "lake", "gorge"]},
        "photography": {"cats": ["viewpoints", "viewpoints-hillstations", "natural-wonders", "mountains", "lakes", "wildlife"], "kw": ["view", "sunrise", "photography", "panorama"]},
        "happy":     {"cats": ["viewpoints", "festivals", "adventure", "cities"], "kw": ["sunrise", "festival", "paragliding", "pokhara", "bazaar"]},
        "excited":   {"cats": ["adventure", "air-sports", "water-sports"], "kw": ["bungee", "zip", "rafting", "paragliding", "skydive"]},
        "solitude":  {"cats": ["lakes", "valleys", "trekking", "trekking-nature", "spiritual-wellness"], "kw": ["remote", "quiet", "high altitude", "lake", "retreat", "rara", "phoksundo", "dolpo", "humla"]},
        "sad":       {"cats": ["spiritual-wellness", "pilgrimage", "lakes", "villages"], "kw": ["peace", "retreat", "meditation", "spiritual", "gompa", "temple"]},
        "energetic": {"cats": ["adventure", "air-sports", "water-sports", "trekking"], "kw": ["rafting", "bungee", "paragliding", "zip", "trek"]},
        "winter":    {"cats": ["winter", "mountains", "trekking"], "kw": ["snow", "winter", "frozen", "kalinchowk"]},
        "snow":      {"cats": ["winter", "mountains"], "kw": ["snow", "winter", "kalinchowk", "poon hill"]},
        "pilgrimage": {"cats": ["pilgrimage", "pilgrimage-and-sacred", "religious-pilgrimage", "temples", "buddhist-sites"], "kw": ["dham", "temple", "mandir", "stupa", "pilgrim"]},
        "lakeside":  {"cats": ["lakes", "lakes-water-bodies"], "kw": ["lake", "phewa", "begnas", "rara", "tilicho", "gokyo"]},
        "food":      {"cats": ["food-culinary", "cities", "shopping"], "kw": ["momo", "food", "bazaar", "market", "culinary", "restaurant"]},
        "festival":  {"cats": ["festivals", "culture"], "kw": ["festival", "jatra", "mela", "dashain", "tihar", "holi"]},
        "shopping":  {"cats": ["shopping", "cities"], "kw": ["bazaar", "market", "shop", "handicraft", "thamel", "asan"]},
        "educational": {"cats": ["museums", "culture", "heritage", "tea-coffee"], "kw": ["research", "center", "science", "pottery", "silk", "museum", "data", "craft"]},
        "nature":    {"cats": ["natural-wonders", "forests", "eco-tourism", "wildlife-and-nature", "lakes", "waterfalls", "caves"], "kw": ["forest", "botanical", "jungle", "rhododendron", "waterfall", "valley", "nature", "cave"]},
        "lakes_rivers": {"cats": ["lakes", "lakes-water-bodies", "rivers", "waterfalls"], "kw": ["lake", "river", "tal", "koshi", "karnali", "gandaki", "waterfall", "jharna"]},
        "history":   {"cats": ["heritage", "heritage-culture", "museums", "cities"], "kw": ["history", "archaeology", "fort", "gadhi", "palace", "durbar", "ancient"]},
        "artisan_crafts": {"cats": ["culture", "heritage", "shopping"], "kw": ["pottery", "thangka", "handicraft", "weaving", "woodcarving", "bronze", "metal"]},
        "village_life": {"cats": ["villages", "eco-tourism", "agriculture"], "kw": ["village", "homestay", "gaun", "community", "traditional", "local", "farm"]},
        "wellness":  {"cats": ["spiritual-wellness", "hot-springs"], "kw": ["meditation", "yoga", "retreat", "spa", "hot spring", "tatopani", "peace"]},
        "camping":   {"cats": ["camping", "natural-wonders", "forests", "trekking"], "kw": ["camp", "tent", "star", "overnight", "outdoor", "trail"]},
        "cycling":   {"cats": ["cycling", "adventure", "scenic-routes"], "kw": ["cycle", "biking", "trail", "circuit", "highway"]},
        "birdwatching": {"cats": ["bird-watching", "wildlife", "wildlife-and-nature", "forests"], "kw": ["bird", "crane", "florican", "wetland", "koshi tappu", "reserve"]},
        # Aliases so the form's interest keys and single words both resolve.
        "relaxation": {"cats": ["lakes", "hot-springs", "spiritual-wellness", "hills"], "kw": ["lake", "peace", "garden", "retreat"]},
        "mountain": {"cats": ["mountains", "adventure-and-mountain", "viewpoints", "trekking"], "kw": ["mountain", "himal", "peak", "himalaya", "alpine"]},
        "mountains": {"cats": ["mountains", "adventure-and-mountain", "viewpoints", "trekking"], "kw": ["mountain", "himal", "peak", "himalaya", "alpine"]},
        "lake": {"cats": ["lakes", "lakes-water-bodies"], "kw": ["lake", "phewa", "begnas", "rara"]},
        "lakes": {"cats": ["lakes", "lakes-water-bodies"], "kw": ["lake", "phewa", "begnas", "rara"]},
        "temple": {"cats": ["temples", "pilgrimage", "religious-pilgrimage"], "kw": ["temple", "mandir", "stupa", "shrine", "dham"]},
        "temples": {"cats": ["temples", "pilgrimage", "religious-pilgrimage"], "kw": ["temple", "mandir", "stupa", "shrine", "dham"]},
        "trek": {"cats": ["trekking", "trekking-nature", "mountains"], "kw": ["trek", "hike", "trail", "base camp", "himal"]},
        "cave": {"cats": ["caves", "natural-wonders"], "kw": ["cave", "gufa", "cavern", "karst"]},
        "caves": {"cats": ["caves", "natural-wonders"], "kw": ["cave", "gufa", "cavern", "karst"]},
        "waterfall": {"cats": ["waterfalls", "natural-wonders", "forests"], "kw": ["waterfall", "falls", "jharana", "chhahara"]},
        "waterfalls": {"cats": ["waterfalls", "natural-wonders", "forests"], "kw": ["waterfall", "falls", "jharana", "chhahara"]},
        "museum": {"cats": ["museums"], "kw": ["museum", "gallery", "exhibition", "archive"]},
        "museums": {"cats": ["museums"], "kw": ["museum", "gallery", "exhibition", "archive"]},
        "food_culinary": {"cats": ["food-culinary"], "kw": ["momo", "thali", "kulfi", "tea", "culinary", "restaurant", "food"]},
        "national_parks": {"cats": ["wildlife", "wildlife-and-nature", "forests", "natural-wonders"], "kw": ["national park", "reserve", "conservation", "safari"]},
        "national-parks": {"cats": ["wildlife", "wildlife-and-nature", "forests", "natural-wonders"], "kw": ["national park", "reserve", "conservation", "safari"]},
        "hill_stations": {"cats": ["hills", "hill-stations-and-views", "viewpoints-hillstations"], "kw": ["hill station", "viewpoint", "hill"]},
        "hill-stations": {"cats": ["hills", "hill-stations-and-views", "viewpoints-hillstations"], "kw": ["hill station", "viewpoint", "hill"]},
        "viewpoint": {"cats": ["viewpoints", "viewpoints-hillstations", "hill-stations-and-views"], "kw": ["viewpoint", "view", "panorama", "sunrise"]},
        "viewpoints": {"cats": ["viewpoints", "viewpoints-hillstations", "hill-stations-and-views"], "kw": ["viewpoint", "view", "panorama", "sunrise"]},
    }

    # "Zoom in" chips the UI sends that are not exact Category slugs. The raw
    # filter used to reject them (national-parks / hill-stations matched no
    # row), so choosing those chips returned nothing. Expand to real slugs.
    CATEGORY_TOKEN_ALIASES = {
        "national-parks": ["wildlife", "wildlife-and-nature", "forests", "natural-wonders"],
        "national_parks": ["wildlife", "wildlife-and-nature", "forests", "natural-wonders"],
        "hill-stations": ["hills", "hill-stations-and-views", "viewpoints-hillstations"],
        "hill_stations": ["hills", "hill-stations-and-views", "viewpoints-hillstations"],
        "lakes-rivers": ["lakes", "lakes-water-bodies", "rivers", "waterfalls"],
        "mountains": ["mountains", "adventure-and-mountain"],
        "viewpoints": ["viewpoints", "viewpoints-hillstations", "hill-stations-and-views"],
        "desert": [],  # Nepal has no deserts; honest empty rather than a wrong category
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
        # Extra explicit category refinement (form-style multi-pick) on top
        # of the mood model: comma/semicolon or + separated slugs/names.
        category_param = request.query_params.get("category") or request.query_params.get("categories") or ""
        requested_categories = [c.strip().lower() for c in re.split(r"[,;+]", category_param) if c.strip()]
        # Season-aware by default: the month being planned, else the legacy
        # season choice, else the current month in Nepal.
        from . import traveller_facts as _tf
        plan_month = _tf.parse_month(request.query_params.get("month"))
        month_basis = "chosen month"
        if plan_month is None and season in {"spring", "summer", "monsoon", "autumn", "winter"}:
            plan_month = {"spring": 4, "summer": 7, "monsoon": 7, "autumn": 10, "winter": 1}[season]
            month_basis = f"{season} (representative month)"
        if plan_month is None:
            from django.utils import timezone as _tz
            plan_month = _tz.localdate().month
            month_basis = "current month"
        travel_style = (request.query_params.get("travel_style") or "any").lower()
        # Exploration mode (frontend ai-recommendation modes): popular /
        # balanced / hidden_gems. It shapes the popularity and novelty
        # signals below instead of being silently ignored.
        exploration_mode = (request.query_params.get("mode") or "balanced").lower()
        province = (request.query_params.get("province") or "").strip().lower()
        persona_param = (request.query_params.get("persona") or request.query_params.get("nationality") or "all").lower()

        # Optional traveller location (master spec §21/§119): when supplied,
        # straight-line proximity joins the ranking and every result carries
        # an honestly labelled distance. Invalid coordinates are ignored, so
        # the endpoint keeps working for visitors who decline to share.
        try:
            traveller_lat = float(request.query_params.get("latitude"))
            traveller_lng = float(request.query_params.get("longitude"))
            if not (-90.0 <= traveller_lat <= 90.0 and -180.0 <= traveller_lng <= 180.0):
                raise ValueError("Coordinates out of range")
        except (TypeError, ValueError):
            traveller_lat = traveller_lng = None

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
        qs = Destination.sightseeing().select_related("category", "risk_analysis").prefetch_related("transit_routes")

        # Aggregate each service relation independently. Joining all three
        # one-to-many tables into the destination query multiplies their rows
        # together (hospitals × police × hotels) while scanning the catalogue.
        service_counts = {}
        for key, model in (
            ("hospital", Hospital),
            ("police", PoliceStation),
            ("hotel", Hotel),
        ):
            service_rows = model.objects.order_by()
            if key in {"hospital", "police"}:
                service_rows = service_rows.filter(is_verified=True, is_archived=False)
            else:
                service_rows = service_rows.filter(
                    is_verified=True, is_active=True, archived_at__isnull=True
                )
            service_counts[key] = dict(
                service_rows
                .values("destination_id")
                .annotate(total=Count("id"))
                .values_list("destination_id", "total")
            )

        exclude_slugs = set(ACCOMMODATION_SLUGS) | set(NON_ATTRACTION_SLUGS)
        qs = qs.exclude(category__slug__in=exclude_slugs)
        for hint in ACCOMMODATION_NAME_HINTS:
            qs = qs.exclude(name__icontains=hint)
        for hint in NON_ATTRACTION_NAME_HINTS:
            qs = qs.exclude(name__icontains=hint)
        if province:
            qs = qs.filter(province__icontains=province)
        if requested_categories:
            # Explicit category pick is a real filter, not just a score bump:
            # what you select is what you can get, so different categories can
            # never return the identical top set.
            #
            # Tokens are normalized first: some UI chips (national-parks,
            # hill-stations) are not Category slugs and used to match zero rows.
            # Aliases expand to real slugs; anything still unknown falls back to
            # a name/description keyword match so a token like "national-parks"
            # still reaches "Chitwan National Park" rows.
            from django.db.models import Q as _Q
            known_slugs = set(Category.objects.values_list("slug", flat=True))
            expanded, text_tokens = set(), []
            for token in requested_categories:
                target = self.CATEGORY_TOKEN_ALIASES.get(token)
                if target is not None:
                    expanded.update(target)
                    continue
                if token in known_slugs:
                    expanded.add(token)
                    continue
                # Unknown token: keep it as a text signal instead of discarding it.
                text_tokens.append(token.replace("-", " "))
            if expanded or text_tokens:
                q = _Q()
                if expanded:
                    q |= _Q(category__slug__in=list(expanded))
                    q |= _Q(category__name__in=list(expanded))
                for token in text_tokens:
                    q |= _Q(name__icontains=token)
                    q |= _Q(short_description__icontains=token)
                    q |= _Q(description__icontains=token)
                    q |= _Q(category__name__icontains=token.replace("-", " "))
                qs = qs.filter(q)

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

        # Narrow the scoring pool to what the request is actually about.
        #
        # Every destination in the country used to be pushed through the full
        # multi-signal scoring loop, which dominated request time. The category
        # signal is worth 0.45 and keywords up to 0.36, so a place in neither
        # the requested categories nor the interest keywords can only reach a
        # low score on season/proximity alone. Pre-selecting category matches,
        # keyword matches, featured places and the most-visited places keeps
        # the ranking honest while cutting the loop to the relevant rows.
        #
        # Only long keywords are used as a SQL filter. Short ones are substring
        # matches in SQL, so "pass" pulls in Pasupatinath and "la" matches
        # half the catalogue, which made broad moods (trekking) slower than the
        # whole-catalogue path they were meant to replace. Short keywords still
        # score inside the loop, so ranking quality is unchanged.
        mood_cat_slugs = set(cat_weights.keys())
        if mood_cat_slugs or kws:
            from django.db.models import Q as _PoolQ
            pool_q = _PoolQ()
            if mood_cat_slugs:
                pool_q |= _PoolQ(category__slug__in=sorted(mood_cat_slugs))
            for kw in [k for k in kws if len(k) >= 5]:
                pool_q |= _PoolQ(name__icontains=kw)
                pool_q |= _PoolQ(short_description__icontains=kw)
            pool_q |= _PoolQ(is_featured=True)
            pool_q |= _PoolQ(id__in=Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED
            ).exclude(category__slug__in=exclude_slugs).order_by("-views_count").values("id")[:120])
            # An explicit category pick is a hard filter already applied above;
            # do not widen it back out here.
            if not requested_categories:
                narrowed = qs.filter(pool_q)
                # Never let the pre-filter empty the page.
                if narrowed.count() >= limit:
                    qs = narrowed

        # Current sourced warnings are distinct from historical/model risk and
        # receive stronger, recency-appropriate ranking influence.
        from django.utils import timezone
        active_hazards = CurrentHazard.objects.filter(is_active=True, verified=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
        ).values("destination_id", "severity", "verified", "source_type", "title")
        severity_order = {"low": 1, "moderate": 2, "high": 3, "critical": 4}
        current_warning_by_destination = {}
        for hazard in active_hazards:
            previous = current_warning_by_destination.get(hazard["destination_id"])
            if previous is None or severity_order.get(hazard["severity"], 0) > severity_order.get(previous["severity"], 0):
                current_warning_by_destination[hazard["destination_id"]] = hazard

        # Shared, sourced facts (season, effort, fees, hospitals, distance).
        # Nothing here is invented: unknown values add no score and no claim.
        from . import traveller_facts as tf
        fact_by_id = {r["id"]: r for r in tf.fact_rows()}
        origin = tf.resolve_origin({
            "origin": request.query_params.get("origin"),
            "origin_lat": request.query_params.get("latitude"),
            "origin_lng": request.query_params.get("longitude"),
        })
        rows = []

        # Every destination's recorded road conditions, in ONE query, for the
        # same reason as the service counts above. The scoring loop runs
        # `qs.iterator(...)`, and `.iterator()` silently disables
        # prefetch_related, so `destination.transit_routes.all()` executed once
        # per row -- roughly 4,783 extra queries, which is why a single
        # recommendation request took 90-110 seconds and routinely timed out in
        # front of a proxy.
        route_conditions_by_destination = {}
        for _dest_id, _condition in DestinationTransitRoute.objects.order_by().values_list(
            "destination_id", "road_condition"
        ):
            if _dest_id is not None and _condition:
                route_conditions_by_destination.setdefault(_dest_id, []).append(_condition)

        # Season guidance only depends on (month, activity, altitude zone,
        # district, province) for its level and score. Thousands of destinations
        # share those, so memoize the numeric verdict for the scoring pass and
        # build the full explainable bundle only for the rows actually returned.
        _zones = _tf.season_dataset()["zones"]
        _season_score_cache = {}

        def season_verdict(facts_row):
            elevation = facts_row["elevation_m"]
            if elevation is None:
                zone = "unknown"
            elif elevation >= _zones["high_altitude_min_m"]:
                zone = "high"
            elif elevation < _zones["tarai_max_m"]:
                zone = "tarai"
            else:
                zone = "mid"
            key = (facts_row["activity"], zone,
                   (facts_row["district"] or "").lower(),
                   (facts_row["province"] or "").lower())
            hit = _season_score_cache.get(key)
            if hit is None:
                fit = _tf.season_fit(month=plan_month, activity=facts_row["activity"],
                                     elevation_m=elevation, district=facts_row["district"],
                                     province=facts_row["province"])
                # level, label, month_name and reason are all built from the
                # constant NTB fact strings plus the booleans captured in the
                # key, so they are identical for every row sharing the key.
                hit = (fit["level"], fit["label"], fit["month_name"], fit["reason"])
                _season_score_cache[key] = hit
            return hit

        for destination in qs.iterator(chunk_size=500):
            facts_row = fact_by_id.get(destination.id)
            if facts_row is None:
                continue
            cat = destination.category.slug if destination.category_id else ""
            hay = f"{destination.name or ''} {destination.short_description or ''} {destination.description or ''} {destination.city or ''} {destination.district or ''}".lower()
            score, reasons, breakdown = 0.05, [], {}

            category_score = 0.45 * min(cat_weights.get(cat, 0), 3.0)
            if category_score:
                score += category_score
                reasons.append(f"Matches your {', '.join(moods[:2])} interests")
            # Explicit form-style category refinement gets a strong, direct lift
            # so a user who picks e.g. "wildlife,heritage" reshapes the ranking.
            cat_name = (destination.category.name or "").lower() if destination.category else ""
            if requested_categories and (cat in requested_categories or cat_name in requested_categories):
                score += 0.30
                reasons.append(f"Matches your requested category: {destination.category.name}")
            # Deterministic-but-fresh personalization: a stable per-(user,month,mood)
            # seed keeps each traveller's ranking distinct and gives different days
            # a slightly different mix, so the same filters no longer return
            # byte-identical results for every user. Near-equal scores reorder.
            import hashlib
            # `request.session` is absent whenever session middleware is not
            # applied (DRF request factories, some ASGI stacks), and an
            # unguarded read raised AttributeError, 500-ing the whole
            # recommendation response. Read every level defensively.
            _session = getattr(request, "session", None)
            _guest_id = (
                request.COOKIES.get("ny_guest_id")
                or getattr(_session, "session_key", None)
                or "anon"
            )
            _user_key = str(request.user.pk) if request.user.is_authenticated else _guest_id
            _fresh = hashlib.sha1(f"{_user_key}|{plan_month}|{'|'.join(moods)}|{destination.id}".encode()).hexdigest()
            score += (int(_fresh, 16) % 1000) / 1000.0 * 0.10
            keyword_hits = [kw for kw in kws if kw in hay]
            keyword_score = min(len(keyword_hits) * 0.09, 0.36)
            score += keyword_score
            if keyword_hits:
                reasons.append("Relevant experiences: " + ", ".join(keyword_hits[:3]))
            breakdown["interests"] = round(category_score + keyword_score, 3)

            # Relevance gate. Category membership is worth 0.45 and keywords up
            # to 0.36, but season (+0.20), proximity (+0.20), popularity and the
            # freshness jitter (+0.10) can add up to ~0.6 on their own. For a
            # narrow interest that let an unrelated place outrank an actual
            # match -- asking for wellness surfaced Attraction and Caves ahead
            # of hot springs. Penalise rows that match neither the requested
            # categories nor the interest keywords, so a match always outranks a
            # non-match. Rows are never dropped, so a thin interest still
            # returns something.
            if cat_weights and not category_score and not keyword_hits:
                score -= 0.55
                breakdown["relevance_gate"] = -0.55

            # Season (NTB climate guidance) for the month being planned.
            # Memoized verdict for scoring; the full explainable bundle is built
            # later, for the rows actually returned.
            season_level, season_label, season_month, season_reason = season_verdict(facts_row)
            season_score = {"best": 0.20, "good": 0.10, "fair": 0.0, "caution": -0.08, "poor": -0.18}[season_level]
            score += season_score
            breakdown["season"] = round(season_score, 3)
            if season_level in {"best", "poor", "caution"}:
                # Good news leads; warnings stay visible right after the match reason.
                reasons.insert(0 if season_level == "best" else min(1, len(reasons)),
                               f"{season_label} in {season_month}: {season_reason}")

            # Effort from measured elevation (unknown elevation = no claim).
            difficulty_info = facts_row["difficulty"]
            inferred_difficulty = difficulty_info["level"]
            wanted = {"hard": "strenuous"}.get(difficulty, difficulty)
            difficulty_score = 0.0
            if wanted != "any" and inferred_difficulty != "unknown":
                difficulty_score = 0.16 if wanted == inferred_difficulty else -0.08
                if wanted == inferred_difficulty:
                    reasons.append(f"{difficulty_info['label']} effort: {difficulty_info['basis']}")
            score += difficulty_score
            breakdown["difficulty"] = difficulty_score

            # Distance from wherever the trip starts (any district or GPS).
            proximity_score, distance_km = 0.0, tf.row_distance(facts_row, origin)
            if distance_km is not None:
                proximity_score = 0.20 * max(0.0, 1.0 - distance_km / 400.0)
                if distance_km <= 60:
                    reasons.append(f"~{distance_km:.0f} km from {origin['label']} (straight line)")
                elif days <= 2 and distance_km > 200:
                    proximity_score -= 0.08
                    reasons.append(f"{distance_km:.0f} km from {origin['label']}: far for a {days}-day trip")
            score += proximity_score
            breakdown["proximity"] = round(proximity_score, 3)

            # Trip length vs NTB acclimatization rules (replaces a guessed duration).
            duration_score = 0.0
            acclim = tf.acclimatization_days(origin.get("elevation_m") if origin else None, facts_row["elevation_m"])
            if acclim and acclim["minimum_days"] > days:
                duration_score = -0.15
                reasons.append(f"Needs at least {acclim['minimum_days']} days of gradual ascent above "
                               f"2,500 m (NTB), longer than your {days}-day trip")
            score += duration_score
            breakdown["duration"] = duration_score

            # Official fees (DOI/NTB rules) instead of invented daily costs.
            cost = facts_row["cost"]
            budget_score = 0.0
            if budget == "low":
                if cost["class"] == "none_on_record":
                    budget_score = 0.08
                    reasons.append("No official permit or park fee on record")
                elif cost["class"] == "restricted_permit":
                    budget_score = -0.12
                    reasons.append(f"Restricted-area permit required ({cost['area']}), charged in USD")
            elif budget == "medium" and cost["class"] == "restricted_permit":
                budget_score = -0.04
            score += budget_score
            breakdown["budget"] = budget_score

            if travel_style == "family" and cat in {"wildlife", "cities", "museums", "parks-gardens", "heritage"}:
                score += 0.14
                reasons.append("Family-friendly experience")
            elif travel_style == "solo" and cat in {"cities", "trekking", "spiritual-wellness"}:
                score += 0.10
                reasons.append("Suitable for solo travel")
            elif travel_style == "couple" and cat in {"lakes", "viewpoints", "hills"}:
                score += 0.12
                reasons.append("Strong couple-trip fit")

            if persona_param in {"nepali", "domestic"}:
                if cat in {"pilgrimage", "spiritual-wellness", "temples", "hill-stations", "villages"}:
                    score += 0.12
                    reasons.append("Top-rated domestic pilgrimage & cultural escape")
                elif cost.get("class") in {"none_on_record", "park_fee"}:
                    score += 0.06
                    reasons.append("Highly accessible domestic destination with nominal entry fees")
            elif persona_param in {"foreign", "international"}:
                if cat in {"mountains", "trekking", "wildlife", "heritage"}:
                    score += 0.10
                    reasons.append("Signature Nepal highlight for international explorers")

            popularity = float(destination.average_rating or 0) * 0.025 + min(math.log10((destination.views_count or 0) + 1) * 0.015, 0.05)
            behavior = min(affinity.get(cat, 0) * 0.025, 0.10)
            # Exploration-mode weighting: leverage popularity/novelty explicitly.
            if exploration_mode == "popular":
                popularity = float(destination.average_rating or 0) * 0.05 + min(math.log10((destination.views_count or 0) + 1) * 0.03, 0.10)
                reasons.append("Popular with travellers")
            elif exploration_mode == "hidden_gems":
                # Reward under-visited, well-kept places; down-weight crowd magnets.
                popularity = float(destination.average_rating or 0) * 0.02
                low_visibility = max(0.0, 0.12 - math.log10((destination.views_count or 0) + 1) * 0.03)
                score += low_visibility
                breakdown["hidden_gem_bonus"] = round(low_visibility, 3)
                if low_visibility > 0:
                    reasons.append("A quieter, less-visited gem")
            else:  # balanced
                popularity = popularity
            score += popularity + behavior
            breakdown["community"] = round(popularity + behavior, 3)

            risk = getattr(destination, "risk_analysis", None)
            risk_level = (risk.risk_category or "low").lower() if risk else "low"
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
                if (
                    warning["severity"] == "critical" and warning["verified"]
                    and warning["source_type"] in {"official", "admin", "api"}
                ):
                    availability = "temporarily_unavailable"
                score += current_warning_adjustment
            breakdown["current_warning_adjustment"] = current_warning_adjustment

            hospital_total = service_counts["hospital"].get(destination.id, 0)
            police_total = service_counts["police"].get(destination.id, 0)
            hotel_total = service_counts["hotel"].get(destination.id, 0)
            service_count = hospital_total + police_total + hotel_total
            emergency_score = min(service_count * 0.015, 0.09)
            score += emergency_score
            breakdown["services"] = round(emergency_score, 3)
            hospital = facts_row["nearest_hospital"]
            if hospital and hospital["verified"] and hospital["km"] <= 10:
                reasons.append(f"Verified hospital on record {hospital['km']} km away")

            elevation_m = facts_row["elevation_m"]
            if elevation_m is not None and elevation_m >= 4000:
                risk_level = "high"
                reasons.append(f"High altitude ({elevation_m:,} m): plan acclimatization")
            elif elevation_m is not None and elevation_m >= 2500:
                risk_level = "moderate"
                reasons.append(f"Above the 2,500 m altitude-sickness threshold ({elevation_m:,} m)")
            elif warning and warning.get("severity") in ["moderate", "high", "critical"]:
                risk_level = warning.get("severity")
            elif risk and risk.risk_category:
                risk_level = risk.risk_category.lower()
            else:
                risk_level = "low"

            if destination.short_description:
                reasons.append(destination.short_description[:120])

            route_records = list(destination.transit_routes.all())
            route_text = " ".join((route.road_condition or "") for route in route_records).lower()
            route_penalty = -0.10 if any(word in route_text for word in ["blocked", "closed", "landslide", "impassable", "dangerous"]) else 0.04 if route_records else 0.0
            score += route_penalty
            breakdown["route_condition"] = route_penalty
            recorded_condition = next((r.road_condition for r in route_records if r.road_condition), None)
            safety_context = {
                "hospital_count": hospital_total,
                "police_count": police_total,
                "hotel_count": hotel_total,
                "route_condition": recorded_condition or "Route condition not on record",
                "route_condition_recorded": bool(recorded_condition),
                "availability": availability,
                "current_warning": {
                    "title": warning["title"], "severity": warning["severity"],
                    "verified": warning["verified"], "source_type": warning["source_type"],
                } if warning else None,
            }
            extra = {"season": _tf.season_fit(month=plan_month, activity=facts_row["activity"],
                                             elevation_m=elevation_m, district=facts_row["district"],
                                             province=facts_row["province"]),
                     "cost": cost, "difficulty": difficulty_info, "acclimatization": acclim,
                     "distance_km": distance_km, "elevation_m": elevation_m}
            rows.append((score, destination, reasons[:5], breakdown, inferred_difficulty, cost["label"], extra, risk_level, safety_context))

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
            score, destination, reasons, breakdown, inferred_difficulty, fee_label, extra, risk_level, safety_context = row
            item["ml_score"] = round(min(score, 1.0), 3)
            item["why_recommended"] = reasons or ["Strong overall match from the live destination catalog"]
            item["match_breakdown"] = breakdown
            item["difficulty"] = inferred_difficulty if inferred_difficulty != "unknown" else None
            item["difficulty_basis"] = extra["difficulty"]["basis"]
            item["official_fees"] = {"label": fee_label, "area": extra["cost"].get("area") or "",
                                     "basis": extra["cost"]["basis"], "source": extra["cost"].get("source")}
            item["budget_level"] = None
            item["season_fit"] = extra["season"]
            item["acclimatization"] = extra["acclimatization"]
            item["elevation_m"] = extra["elevation_m"]
            item["recommended_days"] = destination.recommended_days or None
            item["risk_summary"] = {"level": risk_level, "label": "Historical/model indicator"}
            if destination.latitude is not None and destination.longitude is not None:
                # Answered from the cached facility snapshot. The full
                # build_emergency_directory() ranked every emergency contact and
                # OSM essential-service row and cost ~5.6 s per result, which
                # alone made this endpoint take minutes.
                from .emergency_service import nearest_facilities
                nearby = nearest_facilities(
                    destination.latitude, destination.longitude,
                    radius_km=100, kinds=("hospital", "police"),
                )
                safety_context["nearest_hospital"] = nearby.get("hospital")
                safety_context["nearest_police"] = nearby.get("police")
            item["safety_context"] = safety_context
            item["data_source"] = destination.source or ("User submission" if destination.is_user_submitted else "Database")
            if extra["distance_km"] is not None:
                item["distance_km"] = extra["distance_km"]
                item["distance_is_straight_line"] = True
            data.append(item)
            chosen_rows.append(row)
            if len(data) >= limit:
                break

        return Response({
            "source": "live_database_content_model", "model_version": "content-v3-season",
            "preferences": {"moods": moods, "days": days, "budget": budget, "difficulty": difficulty, "season": season, "travel_style": travel_style, "province": province, "mode": exploration_mode, "category": requested_categories,
                            "month": plan_month, "month_basis": month_basis, "origin": origin,
                            "location": {"latitude": traveller_lat, "longitude": traveller_lng} if traveller_lat is not None else None},
            "season_source": _tf.season_source(),
            "method": ("Content match on your interests, plus NTB season guidance for the month, effort from measured "
                       "elevation, official DOI/NTB fees, NTB acclimatization rules, straight-line distance from your "
                       "starting point, current verified warnings and nearby services. Unknown values add nothing."),
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
    variant = ""
    if len(parts) >= 3:
        # Third part may contain district + optional /id-N suffix
        # Join any remaining parts before id- into district; id- is optional
        extra = "/".join(parts[2:])
        if "/id-" in extra:
            # The id is a seed, not part of the place name: two destinations
            # called "Rupa Lake" in Kaski must not render the same artwork.
            dist, variant = extra.split("/id-", 1)
        elif extra.startswith("id-"):
            dist, variant = "", extra[3:]
        else:
            dist = extra
    svg = generate_postcard_svg(name, cat, dist, variant=variant)
    return HttpResponse(svg, content_type="image/svg+xml; charset=utf-8",
                        headers={"Cache-Control": "public, max-age=86400"})


class TravelerDocumentViewSet(viewsets.ModelViewSet):
    """CRUD for the requesting user's traveler documents (Personal Details page).

    Every queryset is scoped to `request.user`; ownership is also re-checked on
    update/delete via get_object() so one user can never touch another's rows.
    """

    serializer_class = TravelerDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return TravelerDocument.objects.none()
        return TravelerDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------------------------------------------------------------------------
# SEO endpoints (merged from devin dark-mode-compat layer).
# ---------------------------------------------------------------------------

class SitemapView(View):
    """Generated sitemap: static routes + published CMS pages (incl. dynamic
    /page/:key) + published destination slugs. Unpublished pages never appear
    (spec §28: no incorrect exposure)."""

    def get(self, request):
        base = request.build_absolute_uri("/").rstrip("/")
        static = ["", "/destinations", "/districts", "/gallery", "/packages", "/guides",
                  "/about", "/contact", "/emergency", "/discover-nepal", "/explore-map",
                  "/how-it-works", "/knowledge-base"]
        locs = [f"{base}{path}" for path in static]
        for page in ManagedPage.objects.filter(is_enabled=True, status="published"):
            page_data = page.published_snapshot if isinstance(page.published_snapshot, dict) else {}
            key = page_data.get("key") or page.key
            page_route = page_data.get("route") or page.route
            if not page_route:
                continue
            route = page_route if page_route.startswith("/page/") or page_route in static else f"/page/{key}"
            locs.append(f"{base}{route}")
        for slug in Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED).values_list("slug", flat=True)[:5000]:
            locs.append(f"{base}/destinations/{slug}")
        xml = "\n".join(
            ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
            + [f"  <url><loc>{loc}</loc></url>" for loc in dict.fromkeys(locs)]
            + ["</urlset>"]
        )
        return HttpResponse(xml, content_type="application/xml")


class RobotsTxtView(View):
    def get(self, request):
        base = request.build_absolute_uri("/").rstrip("/")
        body = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /staff\n\n" + f"Sitemap: {base}/api/v1/seo/sitemap.xml\n"
        return HttpResponse(body, content_type="text/plain")

class WeatherForecastView(APIView):
    """GET /api/v1/weather/forecast/?lat=27.7172&lon=85.3240&days=5

    Returns a daily aggregated weather forecast using OpenWeatherMap's
    5-day/3-hour forecast API. Falls back to current weather if forecast
    is unavailable. Results are cached for 30 minutes.
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .utils import get_current_weather, validate_nepal_coordinates

        lat = request.query_params.get("lat") or request.query_params.get("latitude")
        lon = request.query_params.get("lon") or request.query_params.get("longitude")

        if lat is None or lon is None:
            return Response(
                {"error": {"code": "missing_parameters", "message": "lat and lon are required", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return Response(
                {"error": {"code": "invalid_parameters", "message": "lat and lon must be numeric", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate coordinates
        validation = validate_nepal_coordinates(lat, lon)
        if not validation["valid"]:
            return Response(
                {"error": {"code": "invalid_coordinates", "message": validation["reason"], "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            days = int(request.query_params.get("days", 5))
            days = max(1, min(days, 7))
        except (TypeError, ValueError):
            days = 5

        # Cache results for 30 minutes
        cache_key = f"weather_forecast:{round(lat, 2)}:{round(lon, 2)}:{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        # Try to get forecast from OpenWeatherMap
        forecast_data = self._fetch_forecast(lat, lon, days)

        if forecast_data is None:
            # Fall back to current weather
            current = get_current_weather(lat, lon)
            if current is None:
                return Response(
                    {"error": {"code": "weather_unavailable", "message": "Weather service is currently unavailable", "details": {}}},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            forecast_data = {
                "source": "current_weather_fallback",
                "days": [{
                    "date": timezone.now().strftime("%Y-%m-%d"),
                    "temp_min": current.get("temperature_c"),
                    "temp_max": current.get("temperature_c"),
                    "condition": current.get("condition"),
                    "description": current.get("description"),
                    "precipitation": 0,
                }],
            }
        else:
            forecast_data["source"] = "openweathermap_forecast"

        forecast_data["cached"] = False
        cache.set(cache_key, forecast_data, 1800)  # 30 minutes
        return Response(forecast_data)

    def _fetch_forecast(self, lat, lon, days):
        """Fetch 5-day/3-hour forecast from OpenWeatherMap and aggregate to daily."""
        import requests

        if not settings.OPENWEATHER_API_KEY:
            return None

        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("cod") != "200":
                return None

            # Aggregate 3-hour forecasts into daily
            daily_data = {}
            for item in data.get("list", []):
                date_str = item["dt_txt"][:10]  # "YYYY-MM-DD"
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        "date": date_str,
                        "temp_min": item["main"]["temp_min"],
                        "temp_max": item["main"]["temp_max"],
                        "conditions": [],
                        "descriptions": [],
                        "precipitation": 0,
                    }
                day = daily_data[date_str]
                day["temp_min"] = min(day["temp_min"], item["main"]["temp_min"])
                day["temp_max"] = max(day["temp_max"], item["main"]["temp_max"])
                if item.get("weather"):
                    day["conditions"].append(item["weather"][0]["main"])
                    day["descriptions"].append(item["weather"][0]["description"])
                if item.get("rain", {}).get("3h"):
                    day["precipitation"] += item["rain"]["3h"]

            # Pick most common condition for each day
            result = []
            for date_str, day in daily_data.items():
                if day["conditions"]:
                    from collections import Counter
                    most_common = Counter(day["conditions"]).most_common(1)[0][0]
                    day["condition"] = most_common
                    day["description"] = day["descriptions"][day["conditions"].index(most_common)]
                else:
                    day["condition"] = "Unknown"
                    day["description"] = ""
                del day["conditions"]
                del day["descriptions"]
                result.append(day)

            return {"days": result[:days]}

        except (requests.RequestException, KeyError, IndexError) as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Weather forecast fetch failed: %s", exc)
            return None


class BulkExportView(APIView):
    """GET /api/v1/admin/export/?type=destinations&format=csv

    Exports data as CSV or JSON. Only accessible by admin users.
    Streams large datasets to avoid memory issues.
    """
    serializer_class = None
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        export_type = request.query_params.get("type", "destinations")
        export_format = request.query_params.get("format", "csv")

        if export_type not in ("destinations", "hotels", "bookings", "reviews"):
            return Response(
                {"error": {"code": "invalid_type", "message": "Type must be one of: destinations, hotels, bookings, reviews", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if export_format not in ("csv", "json"):
            return Response(
                {"error": {"code": "invalid_format", "message": "Format must be csv or json", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if export_format == "csv":
            return self._export_csv(export_type)
        return self._export_json(export_type)

    def _export_csv(self, export_type):
        """Export data as CSV using StreamingHttpResponse."""
        import csv
        import io

        def generate_rows():
            output = io.StringIO()
            writer = csv.writer(output)

            if export_type == "destinations":
                writer.writerow(["id", "name", "slug", "category", "district", "province", "city", "latitude", "longitude", "average_rating", "status"])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                for dest in Destination.publicly_visible().iterator(chunk_size=500):
                    writer.writerow([dest.id, dest.name, dest.slug, dest.category.name if dest.category else "", dest.district or "", dest.province or "", dest.city or "", dest.latitude or "", dest.longitude or "", dest.average_rating, dest.status])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
            elif export_type == "hotels":
                writer.writerow(["id", "name", "destination", "price_per_night", "rating", "booking_status", "is_verified"])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                for hotel in Hotel.objects.select_related("destination").iterator(chunk_size=500):
                    writer.writerow([hotel.id, hotel.name, hotel.destination.name if hotel.destination else "", hotel.price_per_night or "", hotel.rating or "", hotel.booking_status, hotel.is_verified])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
            elif export_type == "bookings":
                from booking.models import Booking
                writer.writerow(["id", "user_email", "hotel", "check_in", "check_out", "guests", "status", "total_price"])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                for booking in Booking.objects.select_related("user", "hotel").iterator(chunk_size=500):
                    writer.writerow([booking.id, booking.user.email, booking.hotel.name, booking.check_in, booking.check_out, booking.guests, booking.status, booking.total_price or ""])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
            elif export_type == "reviews":
                writer.writerow(["id", "destination", "user_email", "comment", "moderation_status", "created_at"])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                for review in Review.objects.select_related("destination", "user").iterator(chunk_size=500):
                    writer.writerow([review.id, review.destination.name if review.destination else "", review.user.email, review.comment[:100], review.moderation_status, review.created_at])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)

        response = StreamingHttpResponse(generate_rows(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{export_type}_export.csv"'
        return response

    def _export_json(self, export_type):
        """Export data as JSON using StreamingHttpResponse."""
        import json

        def generate_json():
            yield "["
            first = True

            if export_type == "destinations":
                for dest in Destination.publicly_visible().iterator(chunk_size=500):
                    if not first:
                        yield ","
                    first = False
                    yield json.dumps({
                        "id": dest.id, "name": dest.name, "slug": dest.slug,
                        "category": dest.category.name if dest.category else None,
                        "district": dest.district, "province": dest.province,
                        "city": dest.city, "latitude": str(dest.latitude) if dest.latitude else None,
                        "longitude": str(dest.longitude) if dest.longitude else None,
                        "average_rating": str(dest.average_rating), "status": dest.status,
                    })
            elif export_type == "hotels":
                for hotel in Hotel.objects.select_related("destination").iterator(chunk_size=500):
                    if not first:
                        yield ","
                    first = False
                    yield json.dumps({
                        "id": hotel.id, "name": hotel.name,
                        "destination": hotel.destination.name if hotel.destination else None,
                        "price_per_night": str(hotel.price_per_night) if hotel.price_per_night else None,
                        "rating": str(hotel.rating) if hotel.rating else None,
                        "booking_status": hotel.booking_status, "is_verified": hotel.is_verified,
                    })
            elif export_type == "bookings":
                from booking.models import Booking
                for booking in Booking.objects.select_related("user", "hotel").iterator(chunk_size=500):
                    if not first:
                        yield ","
                    first = False
                    yield json.dumps({
                        "id": booking.id, "user_email": booking.user.email,
                        "hotel": booking.hotel.name, "check_in": str(booking.check_in),
                        "check_out": str(booking.check_out), "guests": booking.guests,
                        "status": booking.status, "total_price": str(booking.total_price) if booking.total_price else None,
                    })
            elif export_type == "reviews":
                for review in Review.objects.select_related("destination", "user").iterator(chunk_size=500):
                    if not first:
                        yield ","
                    first = False
                    yield json.dumps({
                        "id": review.id, "destination": review.destination.name if review.destination else None,
                        "user_email": review.user.email, "comment": review.comment,
                        "moderation_status": review.moderation_status, "created_at": review.created_at.isoformat(),
                    })

            yield "]"

        response = StreamingHttpResponse(generate_json(), content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="{export_type}_export.json"'
        return response


class ReviewModerationView(APIView):
    """GET/POST /api/v1/admin/review-moderation/

    GET: Lists reviews with moderation_status=pending
    POST: Approve/reject a review with 'action' parameter
    Only accessible by admin/staff users.
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = None

    def get(self, request):
        pending_reviews = Review.objects.filter(
            moderation_status="pending"
        ).select_related("destination", "user").order_by("-created_at")[:100]

        data = [{
            "id": r.id,
            "destination": r.destination.name if r.destination else None,
            "user_email": r.user.email,
            "comment": r.comment,
            "moderation_status": r.moderation_status,
            "created_at": r.created_at.isoformat(),
        } for r in pending_reviews]

        return Response({"reviews": data, "count": len(data)})

    def post(self, request):
        review_id = request.data.get("review_id")
        action = request.data.get("action")
        note = request.data.get("note", "")

        if not review_id:
            return Response(
                {"error": {"code": "missing_review_id", "message": "review_id is required", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in ("approve", "reject"):
            return Response(
                {"error": {"code": "invalid_action", "message": "action must be 'approve' or 'reject'", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            review = Review.objects.select_related("destination", "user").get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Review not found", "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if action == "approve":
            review.moderation_status = "approved"
        else:
            review.moderation_status = "flagged"

        review.moderation_note = note
        review.moderated_by = request.user
        review.moderated_at = timezone.now()
        review.save(update_fields=["moderation_status", "moderation_note", "moderated_by", "moderated_at", "updated_at"])

        return Response({
            "message": f"Review {action}d successfully",
            "review_id": review.id,
            "moderation_status": review.moderation_status,
        })


class HealthCheckView(APIView):
    """GET /api/v1/health/

    Checks database connectivity, cache connectivity, and static files presence.
    Returns {"status": "healthy", "checks": {...}}
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        checks = {}
        all_healthy = True

        # Check database connectivity
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = {"status": "healthy", "message": "Database connection successful"}
        except Exception as exc:
            checks["database"] = {"status": "unhealthy", "message": str(exc)}
            all_healthy = False

        # Check cache connectivity
        try:
            cache.set("health_check", "ok", 10)
            cache_value = cache.get("health_check")
            if cache_value == "ok":
                checks["cache"] = {"status": "healthy", "message": "Cache connection successful"}
            else:
                checks["cache"] = {"status": "unhealthy", "message": "Cache read/write mismatch"}
                all_healthy = False
        except Exception as exc:
            checks["cache"] = {"status": "unhealthy", "message": str(exc)}
            all_healthy = False

        # Check static files presence
        try:
            import os
            static_root = settings.STATIC_ROOT
            if os.path.exists(static_root) and os.path.isdir(static_root):
                static_files = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])
                checks["static_files"] = {"status": "healthy", "message": f"Static files directory exists with {static_files} files"}
            else:
                checks["static_files"] = {"status": "warning", "message": "Static files directory does not exist (may be expected in development)"}
        except Exception as exc:
            checks["static_files"] = {"status": "unhealthy", "message": str(exc)}
            all_healthy = False

        response_data = {
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "timestamp": timezone.now().isoformat(),
        }

        return Response(response_data, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)


class LocationHistoryView(APIView):
    """GET/POST /api/v1/location-history/

    GET: Returns user's location history (paginated, last 100)
    POST: Records a new location (with validation)
    """
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import LocationHistory

        # Rate limit: 30 requests per minute per user
        allowed, remaining, reset_in = _check_rate_limit(
            f"location_history:{request.user.id}", 30, 60
        )
        if not allowed:
            return Response(
                {"error": {"code": "rate_limit_exceeded", "message": "Too many requests. Please try again later.", "details": {"reset_in": reset_in}}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        history = LocationHistory.objects.filter(
            user=request.user
        ).order_by("-recorded_at")[:100]

        data = [{
            "id": h.id,
            "latitude": str(h.latitude),
            "longitude": str(h.longitude),
            "accuracy_m": h.accuracy_m,
            "source": h.source,
            "recorded_at": h.recorded_at.isoformat(),
            "created_at": h.created_at.isoformat(),
        } for h in history]

        return Response({
            "locations": data,
            "count": len(data),
        })

    def post(self, request):
        from .models import LocationHistory
        from .utils import validate_nepal_coordinates

        lat = request.data.get("latitude") or request.data.get("lat")
        lon = request.data.get("longitude") or request.data.get("lon")
        accuracy = request.data.get("accuracy_m")
        source = request.data.get("source", "gps")

        if lat is None or lon is None:
            return Response(
                {"error": {"code": "missing_coordinates", "message": "latitude and longitude are required", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate coordinates
        validation = validate_nepal_coordinates(lat, lon)
        if not validation["valid"]:
            return Response(
                {"error": {"code": "invalid_coordinates", "message": validation["reason"], "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if source not in ("gps", "geoip", "manual"):
            source = "gps"

        try:
            lat = float(lat)
            lon = float(lon)
            accuracy = float(accuracy) if accuracy is not None else None
        except (TypeError, ValueError):
            return Response(
                {"error": {"code": "invalid_parameters", "message": "Coordinates must be numeric", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        location = LocationHistory.objects.create(
            user=request.user,
            latitude=lat,
            longitude=lon,
            accuracy_m=accuracy,
            source=source,
            recorded_at=timezone.now(),
        )

        return Response({
            "id": location.id,
            "latitude": str(location.latitude),
            "longitude": str(location.longitude),
            "accuracy_m": location.accuracy_m,
            "source": location.source,
            "recorded_at": location.recorded_at.isoformat(),
            "message": "Location recorded successfully",
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """DELETE /api/v1/location-history/ — the traveller's own clear button.

        Only the caller's rows are removed, and the deletion is audited so a
        privacy-data clear is traceable rather than silent.
        """
        from .models import LocationHistory

        qs = LocationHistory.objects.filter(user=request.user)
        removed = qs.count()
        qs.delete()
        try:
            from audit.logging_services import log_action
            log_action(
                request=request, action="location_history.clear",
                category="users", severity="warning",
                message=f"Cleared {removed} location history record(s)",
                object_type="LocationHistory",
                extra={"removed": removed},
            )
        except Exception:  # auditing must never block a privacy action
            pass
        return Response({"removed": removed, "message": "Location history cleared"})


class EnhancedSearchView(APIView):
    """GET /api/v1/search/enhanced/?q=pokhara&category=trekking&district=Gandaki&min_rating=4&sort=distance

    Enhanced search with filters:
    - category: Filter by category slug
    - district: Filter by district name
    - min_rating: Minimum average rating
    - max_rating: Maximum average rating
    - has_images: Only show destinations with images
    - verified_only: Only show verified destinations
    - Sort by: relevance, rating, distance, popularity
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Rate limit: 30 requests per minute per IP
        client_ip = self._get_client_ip(request)
        allowed, remaining, reset_in = _check_rate_limit(
            f"search:{client_ip}", 30, 60
        )
        if not allowed:
            return Response(
                {"error": {"code": "rate_limit_exceeded", "message": "Too many search requests. Please try again later.", "details": {"reset_in": reset_in}}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        query = request.query_params.get("q", "").strip()
        category = request.query_params.get("category", "").strip()
        district = request.query_params.get("district", "").strip()
        min_rating = request.query_params.get("min_rating")
        max_rating = request.query_params.get("max_rating")
        has_images = request.query_params.get("has_images", "").lower() in ("true", "1", "yes")
        verified_only = request.query_params.get("verified_only", "").lower() in ("true", "1", "yes")
        sort_by = request.query_params.get("sort", "relevance")
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        # Start with publicly visible destinations
        qs = Destination.publicly_visible().select_related("category").prefetch_related("gallery")

        # Text search
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(city__icontains=query)
                | Q(district__icontains=query)
                | Q(aliases__icontains=query)
            )

        # Apply filters
        if category:
            qs = qs.filter(category__slug__iexact=category)
        if district:
            qs = qs.filter(district__icontains=district)
        if min_rating:
            try:
                qs = qs.filter(average_rating__gte=float(min_rating))
            except (TypeError, ValueError):
                pass
        if max_rating:
            try:
                qs = qs.filter(average_rating__lte=float(max_rating))
            except (TypeError, ValueError):
                pass
        if has_images:
            qs = qs.filter(gallery__isnull=False).distinct()
        if verified_only:
            qs = qs.filter(coordinate_status__in=["VERIFIED", "OFFICIAL", "COMMUNITY_VERIFIED"])

        # Apply sorting
        if sort_by == "rating":
            qs = qs.order_by("-average_rating", "-views_count")
        elif sort_by == "popularity":
            qs = qs.order_by("-views_count", "-average_rating")
        elif sort_by == "distance" and lat and lon:
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                # Annotate with distance using raw SQL for performance
                from django.db.models import FloatField
                from django.db.models.functions import Cast
                qs = qs.annotate(
                    distance=Cast(
                        F("latitude") * 0.0174533, output_field=FloatField()
                    ) * 0 + Cast(
                        F("longitude") * 0.0174533, output_field=FloatField()
                    ) * 0 + Cast(
                        (F("latitude") - lat_f) * 111.0, output_field=FloatField()
                    ) ** 2 + Cast(
                        (F("longitude") - lon_f) * 111.0 * 0.7071, output_field=FloatField()
                    ) ** 2
                ).order_by("distance")
            except (TypeError, ValueError):
                qs = qs.order_by("-average_rating")
        else:
            # Default: relevance (by views and rating)
            qs = qs.order_by("-views_count", "-average_rating")

        # Paginate
        from .pagination import StandardResultsPagination
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = DestinationListSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)

        serializer = DestinationListSerializer(qs[:50], many=True, context={"request": request})
        return Response({"results": serializer.data, "count": len(serializer.data)})

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
