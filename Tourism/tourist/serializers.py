"""
Common serializer mixins and utilities.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .image_server import image_server_url
from .models import (
    User, Language, Category, Destination, DestinationImage, DestinationVideo,
    DestinationTranslation, Review, Rating, Favorite, VisitHistory, Budget,
    Alert, EmergencyContact, Notification, NotificationPreference, DeviceToken, Hospital,
    PoliceStation, Hotel,
    OSMEssentialService, OSMTourismPlace, DestinationAuditLog,
    TravelExpenseFeedback, TravelRiskFeedback, InfrastructureSubmission, InfrastructureMedia,
    CurrentHazard, RiskIncident, RiskObservation, RecommendationEvent, RiskNewsReport,
    SiteSetting, ManagedPage, ContentSection, ManagedNavigationItem, CMSContentTranslation, DestinationFeatureProfile, StaffCapabilityProfile,
    Restaurant, DestinationTransitRoute, TravelPlan, TravelPlanStop, HeroSlide,
    TravelerDocument, RedirectRule, NewsletterSignup, MLInsight,
    RouteSegment,
    FeaturedDestination,
    MarketplaceListing,
)
from .utils import haversine_distance, public_media_url, resolve_image_url


class UsablePhoneMixin:
    """Guarantee that a serialized ``phone`` is either real or empty.

    The imported service data shipped three kinds of unusable value (see
    tourist/phone_quality.py): templated filler, the literal string "nan"
    from a stringified null, and float-mangled real numbers. The first two
    must never be shown as callable; the third is repaired rather than
    displayed with its ".0".

    Everything funnels through :func:`phone_quality.usable_phone`, which is
    also what ``Hospital.save()``/``PoliceStation.save()`` apply, so the read
    path and the stored value can never disagree.
    """

    def to_representation(self, instance):
        from .phone_quality import usable_phone

        data = super().to_representation(instance)
        if "phone" in data:
            data["phone"] = usable_phone(data.get("phone"))
        return data


class TimestampSerializerMixin:
    """Adds created_at and updated_at fields to a serializer."""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserSerializerMixin:
    """Adds user information to a serializer."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        if hasattr(obj, "user") and obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return None


class SoftDeleteSerializerMixin:
    """Adds soft delete fields to a serializer."""

    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)


class AuditSerializerMixin:
    """Adds audit fields to a serializer."""

    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        if hasattr(obj, "created_by") and obj.created_by:
            return obj.created_by.email
        return None

    def get_updated_by(self, obj):
        if hasattr(obj, "updated_by") and obj.updated_by:
            return obj.updated_by.email
        return None


# ---------------------------------------------------------------------------
# Model Serializers
# ---------------------------------------------------------------------------
class CoordinateField(serializers.DecimalField):
    """
    Safe coordinate parser and validator. Handles raw floats, strings,
    NaNs, nulls, and quantizes to 6 decimal places safely.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 9)
        kwargs.setdefault("decimal_places", 6)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data in (None, "", "null", "undefined", "NaN", "nan"):
            if not self.required or self.allow_null:
                return None
            raise serializers.ValidationError("A valid numeric coordinate is required.")
        try:
            val = float(str(data).strip())
            import math
            if math.isnan(val) or math.isinf(val):
                if not self.required or self.allow_null:
                    return None
                raise serializers.ValidationError("A valid numeric coordinate is required.")
            data = Decimal(str(round(val, 6))).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            return super().to_internal_value(data)
        except Exception:
            if not self.required or self.allow_null:
                return None
            raise serializers.ValidationError("Invalid coordinate value.")


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "code", "name", "is_active"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description"]


def _approved_gallery(obj):
    """Approved gallery photos with the admin-designated cover first.

    The detail contract (`DestinationCoverImagePriorityTests`) promises
    `images[0]` is the cover the admin picked, then the rest in ordering.
    """
    gallery = getattr(obj, "gallery", None)
    if gallery is None:
        return []
    photos = [
        p
        for p in gallery.all()
        if getattr(p, "verification_status", "approved") == "approved"
    ]
    photos.sort(
        key=lambda p: (
            not getattr(p, "is_cover", False),
            getattr(p, "ordering", 0) or 0,
            getattr(p, "id", 0) or 0,
        )
    )
    return photos


def _photo_url(photo, request=None):
    """One DestinationImage -> a URL that actually loads.

    Imported media lives in `external_url` and must pass through verbatim:
    Django's `ImageField.url` would emit `/media/https%3A%2F%2F...` for rows
    whose stored value is already an absolute URL, which 404s. `image_path`
    rows are resolved to a same-origin `/media/...` path -- never through
    image_server_url(), whose unset IMAGE_BASE_URL falls back to
    http://localhost:8000 and would hand every visitor a dead host.
    """
    from .utils import public_media_url, resolve_image_url

    external = getattr(photo, "external_url", "") or ""
    if external:
        return external
    if getattr(photo, "image", None):
        resolved = resolve_image_url(photo.image, request)
        if resolved:
            return resolved
    if getattr(photo, "image_path", ""):
        return public_media_url(photo.image_path)
    return ""


def destination_cover_image(obj, request=None):
    """Resolve the cover URL: admin-set Destination.cover_image first (admin
    commands write URLs straight into that column), else the approved cover
    photo, else the first approved photo, else None.

    The gallery fallback runs through ``verified_destination_photos`` so a
    cover must be approved, verified AND destination-specific: a Rara Lake
    photo attached to a Kaski trek must never surface as its cover
    (``test_cross_destination_image_is_not_used_as_fallback``).  None rather
    than "" so callers can assert true absence.
    """
    from .utils import resolve_image_url

    if getattr(obj, "cover_image", None):
        resolved = resolve_image_url(obj.cover_image, request)
        if resolved:
            return resolved
    photos = verified_destination_photos(obj)
    cover = next((photo for photo in photos if photo.is_cover), None) or (photos[0] if photos else None)
    if cover:
        return _photo_url(cover, request) or None
    return None


def _cover_cached(obj, request=None):
    """Memoise the cover on the row so `cover_image` + `cover_image_url`
    don't each run their own gallery query for every row of a list page.

    Key presence is the sentinel: a legitimate result is now None (no usable
    media), and `if hit is None` would re-run the gallery query every time."""
    if "_resolved_cover_url" not in obj.__dict__:
        obj.__dict__["_resolved_cover_url"] = destination_cover_image(obj, request)
    return obj.__dict__["_resolved_cover_url"]


def destination_image_urls(obj, request=None):
    """Cover first, then every other approved photo, de-duplicated."""
    urls = []
    cover = _cover_cached(obj, request)
    if cover:
        urls.append(cover)
    for photo in _approved_gallery(obj):
        url = _photo_url(photo, request)
        if url and url not in urls:
            urls.append(url)
    return urls


class DestinationListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image = serializers.SerializerMethodField()
    # The frontend contract is `cover_image_url` (imageUtils, Chatbot,
    # DiscoverNepal, RecommendationCard, CMSBlock, AdminDashboard...); emitting
    # only `cover_image` left every one of those surfaces blank.
    cover_image_url = serializers.SerializerMethodField()
    # Honesty fields: always present in the payload, null unless a recorded
    # source backs them (RecordedPlaceHonestyTests). Dropping the keys made
    # KeyError the tests and blanked DestinationCard/CompareDestinations.
    budget_estimate = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    recommended_season = serializers.SerializerMethodField()
    display_city = serializers.SerializerMethodField()
    has_map_pin = serializers.SerializerMethodField()

    def get_cover_image(self, obj):
        return _cover_cached(obj, self.context.get("request"))

    def get_cover_image_url(self, obj):
        return _cover_cached(obj, self.context.get("request"))

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_budget_estimate(self, obj):
        try:
            budget = obj.budget_estimation
        except Exception:
            budget = None
        if budget:
            value = budget.estimated_daily_budget or budget.estimated_trip_budget
            if value is not None:
                return float(value)
        if obj.entry_fee not in (None, ""):
            try:
                fee = float(obj.entry_fee)
            except (TypeError, ValueError):
                fee = None
            if fee:
                return fee
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_risk_level(self, obj):
        try:
            risk = obj.risk_analysis
        except Exception:
            risk = None
        if risk and risk.risk_category:
            return str(risk.risk_category).lower()
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_recommended_season(self, obj):
        season = (obj.best_time_to_visit or "").strip()
        if not season:
            return None
        if "no record" in season.lower() or "round" in season.lower() or "no verided" in season.lower():
            return "All Seasons (Autumn / Spring)"
        return season

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_display_city(self, obj):
        from .location_sync import display_city
        return display_city(obj) or None

    @extend_schema_field(serializers.BooleanField())
    def get_has_map_pin(self, obj):
        from .location_sync import has_map_pin
        return has_map_pin(obj)

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "city", "district", "country",
            "category_name", "average_rating", "entry_fee", "type",
            "cover_image", "cover_image_url", "is_featured",
            "budget_estimate", "risk_level", "recommended_season",
            "display_city", "has_map_pin",
        ]


class DestinationDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    # Same contract as above, plus what DestinationDetails.jsx and
    # DestinationHero.jsx read to build the hero + verified-photo gallery.
    image_url = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    # Same honesty contract as the list serializer - DestinationDetails.jsx
    # reads display_city, CompareDestinations reads budget_estimate and
    # recommended_season, DestinationSafety reads risk_level.
    budget_estimate = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    recommended_season = serializers.SerializerMethodField()
    display_city = serializers.SerializerMethodField()
    has_map_pin = serializers.SerializerMethodField()
    # Detail-page sections dropped by the same old cleanup: DestinationDetails
    # renders `notices` (place + district visitor warnings) and
    # `marketplace_listings` (published stays/tours) straight from the payload.
    notices = serializers.SerializerMethodField()
    marketplace_listings = serializers.SerializerMethodField()

    def _request(self):
        return self.context.get("request")

    def get_cover_image(self, obj):
        return _cover_cached(obj, self._request())

    def get_cover_image_url(self, obj):
        return _cover_cached(obj, self._request())

    def get_image_url(self, obj):
        return _cover_cached(obj, self._request())

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_budget_estimate(self, obj):
        try:
            budget = obj.budget_estimation
        except Exception:
            budget = None
        if budget:
            value = budget.estimated_daily_budget or budget.estimated_trip_budget
            if value is not None:
                return float(value)
        if obj.entry_fee not in (None, ""):
            try:
                fee = float(obj.entry_fee)
            except (TypeError, ValueError):
                fee = None
            if fee:
                return fee
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_risk_level(self, obj):
        try:
            risk = obj.risk_analysis
        except Exception:
            risk = None
        if risk and risk.risk_category:
            return str(risk.risk_category).lower()
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_recommended_season(self, obj):
        season = (obj.best_time_to_visit or "").strip()
        if not season:
            return None
        if "no record" in season.lower() or "round" in season.lower() or "no verided" in season.lower():
            return "All Seasons (Autumn / Spring)"
        return season

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_display_city(self, obj):
        from .location_sync import display_city
        return display_city(obj) or None

    @extend_schema_field(serializers.BooleanField())
    def get_has_map_pin(self, obj):
        from .location_sync import has_map_pin
        return has_map_pin(obj)

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_notices(self, obj):
        from .notices import notices_for_destination, serialize_notice
        return [serialize_notice(notice) for notice in notices_for_destination(obj)[:12]]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_marketplace_listings(self, obj):
        # Only published listings from approved partners; drafts and
        # unvetted partners must never surface on a public detail page.
        listings = obj.marketplace_listings.filter(
            status=MarketplaceListing.Status.PUBLISHED, partner__status="approved",
        ).select_related("partner")[:8]
        return [{
            "id": item.id, "slug": item.slug, "kind": item.kind, "title": item.title,
            "summary": item.summary, "price_npr": str(item.price_npr), "currency": item.currency,
            "image_url": item.image_url, "duration_days": item.duration_days,
            "partner_name": item.partner.name, "is_featured": item.is_featured,
        } for item in listings]

    def get_images(self, obj):
        return destination_image_urls(obj, self._request())

    def get_gallery(self, obj):
        request = self._request()
        out = []
        for photo in _approved_gallery(obj):
            url = _photo_url(photo, request)
            if not url:
                continue
            out.append(
                {
                    "id": getattr(photo, "id", None),
                    "image": url,
                    "external_url": getattr(photo, "external_url", "") or None,
                    "display_url": url,
                    # DestinationDetails.jsx reads caption/photographer/
                    # source/license_type; DestinationImage stores alt_text
                    # and source, everything else falls back in the UI.
                    "caption": getattr(photo, "alt_text", "") or None,
                    "source": getattr(photo, "source", "") or None,
                    "photographer": getattr(photo, "photographer", "") or None,
                    "license_type": getattr(photo, "license_type", "") or None,
                    "image_category": getattr(photo, "image_category", "") or None,
                    "is_cover": bool(getattr(photo, "is_cover", False)),
                    "verification_status": getattr(photo, "verification_status", "approved"),
                }
            )
        return out

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "description", "short_description",
            "city", "district", "province", "municipality", "country",
            "category_name", "type", "average_rating", "ratings_count",
            "views_count", "cover_image", "cover_image_url", "image_url",
            "images", "gallery", "latitude", "longitude",
            "coordinate_status", "coordinate_source", "coordinate_accuracy",
            "address", "opening_hours", "entry_fee", "recommended_days",
            "best_time_to_visit", "altitude", "elevation_m",
            "distance_from_kathmandu_km", "distance_from_nearest_city_km",
            "nearest_major_city", "distance_from_nearest_airport_km",
            "nearest_airport_name", "approx_travel_time",
            "nearest_hospital_info", "nearest_police_info", "nearest_hotel_info",
            "history", "cultural_significance", "religious_significance",
            "tourism_importance", "food_cuisine_info", "travel_safety_tips",
            "location_notes", "seo_title", "meta_description", "og_image_url",
            "meta_robots", "search_visible",
            "budget_estimate", "risk_level", "recommended_season",
            "display_city", "has_map_pin",
            "notices", "marketplace_listings",
            "is_featured", "is_active", "status", "created_at", "updated_at",
        ]


class DestinationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["name", "description", "short_description", "city", "country", "category", "latitude", "longitude", "address", "opening_hours", "entry_fee"]

    def create(self, validated_data):
        # Submission lifecycle lives here (not in a view) so every write path
        # honours it: staff destinations publish immediately, tourist
        # submissions start pending/inactive and only go live through the
        # approve action. An older cleanup dropped this and every tourist
        # submission auto-published with the model default (approved).
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            validated_data["created_by"] = user
        if user is not None and user.is_authenticated and user.is_staff:
            validated_data["is_user_submitted"] = False
            validated_data["status"] = Destination.SubmissionStatus.APPROVED
        else:
            validated_data["is_user_submitted"] = True
            validated_data["status"] = Destination.SubmissionStatus.PENDING
            validated_data["is_active"] = False
        destination = super().create(validated_data)

        if user is not None and user.is_authenticated:
            DestinationAuditLog.objects.create(
                destination=destination, action=DestinationAuditLog.Action.SUBMITTED,
                actor=user, new_status=destination.status,
            )
        return destination


class DestinationApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["status", "review_note"]


class DestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationImage
        fields = ["id", "destination", "image", "external_url", "alt_text", "ordering", "is_cover", "source", "verification_status"]


class DestinationVideoSerializer(serializers.ModelSerializer):
    display_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = DestinationVideo
        fields = [
            "id", "destination", "video_url", "video_file", "display_url", "title", "caption",
            "thumbnail", "uploaded_by", "uploaded_by_name", "verification_status", "created_at",
        ]
        read_only_fields = ["uploaded_by", "verification_status", "created_at"]

    def get_display_url(self, obj):
        request = self.context.get("request")
        if obj.video_file:
            try:
                return request.build_absolute_uri(obj.video_file.url) if request else obj.video_file.url
            except (ValueError, AttributeError):
                return None
        return obj.video_url or None

    def validate(self, attrs):
        uploaded = attrs.get("video_file")
        url = (attrs.get("video_url") or getattr(self.instance, "video_url", "") or "").strip()
        existing_file = getattr(self.instance, "video_file", None) if self.instance else None
        if not uploaded and not url and not existing_file:
            raise serializers.ValidationError("Upload a video file (max 25 MB) or provide a video URL.")
        if uploaded and uploaded.size > 25 * 1024 * 1024:
            raise serializers.ValidationError("Videos must be 25 MB or smaller.")
        content_type = (getattr(uploaded, "content_type", "") or "").lower()
        if uploaded and content_type and not content_type.startswith("video/") and content_type not in {"application/octet-stream"}:
            raise serializers.ValidationError("Upload a video file.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["uploaded_by"] = user
            from .views_admin import _has_capability
            approved = _has_capability(request, "images", "approve")
            validated_data["verification_status"] = "approved" if approved else "pending"
        return super().create(validated_data)


class DestinationTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationTranslation
        fields = ["id", "destination", "language", "name", "description", "short_description", "is_auto_generated"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "destination", "user", "user_name", "comment", "is_flagged", "moderation_status", "created_at", "updated_at"]
        read_only_fields = ["user", "is_flagged", "moderation_status", "created_at", "updated_at"]

    def validate_destination(self, destination):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            qs = Review.objects.filter(destination=destination, user=request.user)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "You have already reviewed this destination. Edit your existing review instead."
                )
        return destination


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "destination", "user", "value", "created_at"]
        # `user` comes from the authenticated request in RatingViewSet
        # .perform_create; leaving it writable made every rating POST 400
        # ("user: this field is required") before perform_create ever ran.
        read_only_fields = ["user", "created_at"]

    def validate_destination(self, destination):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            qs = Rating.objects.filter(destination=destination, user=request.user)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "You have already rated this destination. Update your existing rating instead."
                )
        return destination


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["id", "user", "destination", "created_at"]
        # Same contract as RatingViewSet: FavoriteViewSet.perform_create
        # injects the requesting user, so the payload must not require it.
        read_only_fields = ["user", "created_at"]


class VisitHistorySerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = VisitHistory
        fields = ["id", "user", "destination", "destination_name", "viewed_at"]


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [
            "id", "user", "destination", "title", "category", "amount",
            "currency", "date", "notes", "created_at",
        ]
        read_only_fields = ["user", "created_at"]


class AlertSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id", "alert_type", "title", "description", "severity",
            "latitude", "longitude", "city", "country", "municipality", "district", "province",
            "source", "source_url", "is_verified", "radius_km",
            "is_active", "starts_at", "ends_at", "created_at", "distance_km",
        ]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj):
        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")
        if user_lat is None or user_lon is None or obj.latitude is None or obj.longitude is None:
            return None
        try:
            return round(haversine_distance(user_lat, user_lon, obj.latitude, obj.longitude), 2)
        except (ValueError, TypeError):
            return None


class EmergencyContactSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyContact
        fields = [
            "id", "contact_type", "name", "phone_number", "alternate_phone",
            "address", "city", "country", "latitude", "longitude",
            "is_24_hours", "ward_number", "designation", "distance_km",
        ]
    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj):

        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")

        if (
            user_lat is None
            or user_lon is None
            or obj.latitude is None
            or obj.longitude is None
        ):
            return None

        try:
            return round(
                haversine_distance(
                    user_lat,
                    user_lon,
                    obj.latitude,
                    obj.longitude,
                ),
                2,
            )

        except (ValueError, TypeError):
            return None


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user", "title", "message", "channel", "category", "is_read", "is_sent", "delivery_status", "created_at", "read_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["id", "user", "in_app_enabled", "email_enabled", "sms_enabled", "push_enabled", "safety_alerts", "booking_updates", "recommendations", "marketing"]


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "user", "token", "platform", "created_at"]


class NearbyDestinationQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    radius = serializers.FloatField(default=10.0)
    # `radius_km` is the name every view reads out of validated_data
    # (destinations/nearby, alerts/nearby, emergency-contacts/nearest) - the
    # field was renamed to `radius` in an old cleanup, which KeyError'd all
    # three endpoints into 500s. Keep both names so either query param works.
    radius_km = serializers.FloatField(default=10, min_value=0.1, max_value=2000)
    limit = serializers.IntegerField(default=20)


class TranslateRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    source_language = serializers.CharField(required=False, default="en")
    target_language = serializers.CharField()


class PhotoUploadSerializer(serializers.ModelSerializer):
    """
    Used by the community photo-upload endpoint. Any authenticated user can
    submit a photo for a destination; it's tagged `source=user_upload` and
    starts un-promoted — see utils.py::maybe_promote_photo() for how it can
    later become the official cover image based on popularity.

    This is a ModelSerializer over DestinationImage because the view injects
    `destination` (not `destination_id`) into the payload: a plain Serializer
    with a required `destination_id` field 400'd every community upload.
    The model's `image` is blank/null, so a caption-only contribution (the
    documented flow) still validates.
    """

    class Meta:
        model = DestinationImage
        fields = ["id", "destination", "image", "caption"]

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        validated_data["source"] = DestinationImage.Source.USER_UPLOAD
        return super().create(validated_data)


class HotelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image_is_hotel_specific = serializers.SerializerMethodField()
    image_source = serializers.SerializerMethodField()
    destination_context_image_url = serializers.SerializerMethodField()
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    destination_slug = serializers.CharField(source="destination.slug", read_only=True)

    class Meta:
        model = Hotel
        fields = [
            "id",
            "name", "destination", "destination_name", "destination_slug",
            "address",
            "latitude",
            "longitude",
            "price_per_night",
            "currency",
            "rating",
            "booking_status",
            "facilities",
            "booking_url", "cover_image", "external_image_url",
            "image_url", "image_is_hotel_specific", "image_source", "destination_context_image_url",
            "source", "source_url", "is_verified", "verified_at", "is_active", "archived_at", "updated_at",
        ]

    def validate_external_image_url(self, value):
        if value and not value.startswith("https://"):
            raise serializers.ValidationError("Hotel image URL must use HTTPS")
        return value

    def validate_cover_image(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Hotel cover must be 5 MB or smaller")
        content_type = getattr(value, "content_type", "")
        if value and content_type and content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise serializers.ValidationError("Use JPEG, PNG or WebP hotel images")
        return value

    def _hotel_specific_url(self, obj):
        if obj.cover_image:
            return resolve_image_url(obj.cover_image)
        return obj.external_image_url or None

    def _destination_context_url(self, obj):
        if hasattr(obj, "_destination_context_image_cache"):
            return obj._destination_context_image_cache
        result = public_destination_cover(obj.destination, self.context.get("request")) if obj.destination else None
        obj._destination_context_image_cache = result
        return result

    def get_image_url(self, obj):
        # Compatibility display URL. `image_is_hotel_specific` tells clients
        # whether this is actual hotel media or an honestly-labelled area photo.
        return self._hotel_specific_url(obj) or self._destination_context_url(obj)

    def get_image_is_hotel_specific(self, obj):
        return bool(self._hotel_specific_url(obj))

    def get_image_source(self, obj):
        if obj.cover_image: return "hotel_upload"
        if obj.external_image_url: return "hotel_external"
        if self._destination_context_url(obj): return "destination_context"
        return "unavailable"

    def get_destination_context_image_url(self, obj):
        return self._destination_context_url(obj)


class OSMEssentialServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OSMEssentialService
        fields = ["id", "osm_id", "category", "name", "phone", "latitude", "longitude", "address", "is_verified", "is_archived"]


class OSMTourismPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OSMTourismPlace
        fields = ["id", "osm_id", "category", "name", "latitude", "longitude", "address"]


class TravelExpenseFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelExpenseFeedback
        fields = ["id", "user", "destination", "destination_name", "num_people", "num_days", "travel_mode", "accommodation_cost", "travel_cost", "entry_cost", "food_cost", "extra_cost"]


class TravelRiskFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = TravelRiskFeedback
        fields = [
            "id", "user", "user_name", "destination", "destination_name",
            "became_sick", "sickness_type", "misleading_activities",
            "misleading_details", "accident_occurred", "accident_details",
            "hazard_witnessed", "transport_accessibility_rating",
            "people_helpfulness_rating", "greeting_behavior_rating",
            "overall_safety_rating", "comments", "is_admin_verified", "reviewed_by", "reviewed_at", "created_at"
        ]
        read_only_fields = ["user", "is_admin_verified", "reviewed_by", "reviewed_at", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


class InfrastructureMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = InfrastructureMedia
        fields = ["id", "media_type", "file", "file_url", "caption", "is_primary", "is_verified", "created_at"]
        read_only_fields = ["is_verified", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        try:
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        except (ValueError, AttributeError):
            return None


class RiskNewsReportSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = RiskNewsReport
        fields = [
            "id", "destination", "destination_name", "title", "summary", "hazard_type",
            "source_name", "source_url", "published_at", "latitude", "longitude",
            "affected_area", "verification_status", "promoted_to_warning", "created_at", "updated_at",
        ]
        read_only_fields = ["promoted_to_warning", "created_at", "updated_at"]


class DestinationFeatureProfileSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    class Meta:
        model = DestinationFeatureProfile
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "verified_at"]


class RiskIncidentAdminSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    class Meta:
        model = RiskIncident
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class CurrentHazardAdminSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    class Meta:
        model = CurrentHazard
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class RiskObservationAdminSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    class Meta:
        model = RiskObservation
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class RestaurantSerializer(UsablePhoneMixin, serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = Restaurant
        fields = ["id", "destination", "destination_name", "name", "cuisine_types", "description", "address",
                  "phone", "website", "opening_hours", "price_range", "latitude", "longitude",
                  "vegetarian_friendly", "image_url", "source_name", "source_url", "website", "is_verified", "status", "updated_at"]
        read_only_fields = ["is_verified", "status", "updated_at"]


class RouteSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteSegment
        fields = [
            "id", "route", "segment_order", "from_location", "to_location",
            "transport_mode", "distance_km", "duration_mins", "fare_npr", "notes"
        ]


class DestinationTransitRouteSerializer(serializers.ModelSerializer):
    segments = RouteSegmentSerializer(many=True, read_only=True)
    destination_name = serializers.ReadOnlyField(source="destination.name")
    destination_slug = serializers.ReadOnlyField(source="destination.slug")

    class Meta:
        model = DestinationTransitRoute
        fields = [
            "id", "destination", "destination_name", "destination_slug", "origin",
            "origin_latitude", "origin_longitude", "destination_latitude", "destination_longitude",
            "transport_mode", "distance_km", "approx_duration", "road_condition", "key_stops",
            "estimated_fare_npr", "fare_currency", "route_source", "operator_name",
            "contact_phone", "booking_url", "departure_schedule", "confidence_level",
            "is_active", "is_verified", "verified_at", "expires_at", "updated_at", "segments"
        ]
        read_only_fields = ["updated_at"]


class TravelPlanStopSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = TravelPlanStop
        fields = ["id", "plan", "destination", "destination_name", "transit_route", "day_number", "display_order", "arrival_time", "departure_time", "notes"]

    def validate_plan(self, plan):
        request = self.context.get("request")
        if request and plan.user_id != request.user.id:
            raise serializers.ValidationError("You may only edit your own travel plans")
        return plan


class TravelPlanSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    stops = TravelPlanStopSerializer(many=True, read_only=True)

    class Meta:
        model = TravelPlan
        fields = ["id", "user", "user_email", "title", "start_date", "end_date", "travelers", "budget_npr",
                  "interests", "itinerary_data", "generation_source", "status", "notes", "stops",
                  "share_token", "shared_at", "created_at", "updated_at"]
        # Sharing is changed only through /travel-plans/<id>/share/ (owner only).
        read_only_fields = ["user", "user_email", "status", "share_token", "shared_at", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError("End date cannot be before start date")
        return attrs


class TravelerDocumentSerializer(serializers.ModelSerializer):
    """Personal Details CRUD. `user` is always the request user (set in the
    viewset's perform_create) and never accepted from the client."""

    class Meta:
        model = TravelerDocument
        fields = [
            "id", "full_name", "relation_tag", "relation", "phone",
            "id_type", "id_number", "nationality", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Auth Serializers
# ---------------------------------------------------------------------------
class RegisterSerializer(serializers.Serializer):
    """Create a public tourist account using Django's password hashing.

    This is a plain Serializer because the public registration payload is
    intentionally smaller than the User model. Plain DRF Serializers must
    implement ``create()`` themselves; otherwise ``serializer.save()``
    raises ``NotImplementedError``.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        if validated_data.get("phone_number") in ("", None):
            validated_data["phone_number"] = None
        return User.objects.create_user(password=password, **validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()


class SMSVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)


class UserProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    preferred_language = serializers.CharField(required=False, allow_blank=True)


class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    preferred_language = serializers.CharField(required=False, allow_blank=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ResetPasswordOtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordOtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class VerifyPhoneSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)


class ChangePhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    verification_code = serializers.CharField(max_length=6)


class UpdateLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(required=False)


class UpdatePreferencesSerializer(serializers.Serializer):
    preferred_language = serializers.CharField(required=False, allow_blank=True)
    notification_preferences = serializers.DictField(required=False)


# ---------------------------------------------------------------------------
# Admin Serializers
# ---------------------------------------------------------------------------
class FeaturedDestinationSerializer(serializers.ModelSerializer):
    """Admin Featured Content Studio serializer.

    This targets the FeaturedDestination model. Commit d1a59e9 replaced it with
    a two-liner declaring `model = Destination` plus a field list that exists on
    neither model, so every admin create/update of a featured card died with
    ImproperlyConfigured. Restored to the version the admin panel and the
    FeaturedDestinationTests were written against.
    """

    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all())
    destination_name = serializers.ReadOnlyField(source="destination.name")
    destination_slug = serializers.ReadOnlyField(source="destination.slug")
    destination_city = serializers.ReadOnlyField(source="destination.city")
    destination_province = serializers.ReadOnlyField(source="destination.province")
    destination_district = serializers.ReadOnlyField(source="destination.district")
    destination_rating = serializers.ReadOnlyField(source="destination.average_rating")

    effective_title = serializers.ReadOnlyField()
    effective_description = serializers.ReadOnlyField()
    effective_image_url = serializers.ReadOnlyField()
    effective_cta_url = serializers.ReadOnlyField()

    created_by_email = serializers.ReadOnlyField(source="created_by.email")
    updated_by_email = serializers.ReadOnlyField(source="updated_by.email")

    class Meta:
        model = FeaturedDestination
        fields = [
            "id", "destination", "destination_name", "destination_slug",
            "destination_city", "destination_province", "destination_district", "destination_rating",
            "title", "short_description", "featured_media", "featured_media_url",
            "effective_title", "effective_description", "effective_image_url", "effective_cta_url",
            "cta_label", "cta_url", "display_order", "is_published",
            "publish_start", "publish_end", "created_at", "updated_at",
            "created_by", "created_by_email", "updated_by", "updated_by_email",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "updated_by"]

    def to_internal_value(self, data):
        # The admin panel (and the API tests) send `destination_id`; the model
        # relation is `destination`.
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if "destination_id" in data and "destination" not in data:
            data["destination"] = data["destination_id"]
        return super().to_internal_value(data)

    def validate(self, attrs):
        destination = attrs.get("destination") or (self.instance.destination if self.instance else None)
        if not destination:
            raise serializers.ValidationError({"destination": "An existing destination must be selected."})

        if not self.instance:
            existing = FeaturedDestination.objects.filter(destination=destination).first()
            if existing:
                raise serializers.ValidationError({"destination": f"Destination '{destination.name}' is already configured as featured (ID #{existing.id})."})

        p_start = attrs.get("publish_start") or (self.instance.publish_start if self.instance else None)
        p_end = attrs.get("publish_end") or (self.instance.publish_end if self.instance else None)
        if p_start and p_end and p_start >= p_end:
            raise serializers.ValidationError({"publish_end": "publish_end must be later than publish_start."})

        return attrs


class InfrastructureSubmissionSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source="submitted_by.full_name", read_only=True)
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    media = InfrastructureMediaSerializer(many=True, read_only=True)

    class Meta:
        model = InfrastructureSubmission
        fields = "__all__"
        read_only_fields = [
            "submitted_by", "status", "admin_note", "reviewed_by", "reviewed_at",
            "published_model", "published_object_id", "csv_synced_at", "created_at", "updated_at",
        ]

    def _url(self, field):
        if not field:
            return None
        request = self.context.get("request")
        try:
            return request.build_absolute_uri(field.url) if request else field.url
        except (ValueError, AttributeError):
            return None

    def get_image_url(self, obj):
        return self._url(obj.image)

    def get_video_url(self, obj):
        return self._url(obj.video)

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["submitted_by"] = request.user
        return super().create(validated_data)


#: Generated SVG postcards are served from this route and are stored on the
#: row as ``external_url`` (the data-repair scripts filter on this prefix).
POSTCARD_URL_MARKER = "/api/v1/postcard/"

#: Older/other shapes that also denote generated placeholder imagery rather
#: than photography of the place.
_POSTCARD_LEGACY_MARKERS = ("/postcards/", "/media/postcards/", "postcard://")


def is_generated_postcard_url(url):
    """True for generated SVG postcard placeholder URLs.

    Postcards are an honest "no real photo yet" state: they must never be
    served as destination photography (spec: generated media is rejected as
    real photography; a postcard-only destination renders as an empty/
    placeholder state on the public site, not as fake imagery).
    """
    if not url:
        return False
    text = str(url)
    return (
        POSTCARD_URL_MARKER in text
        or text.startswith(_POSTCARD_LEGACY_MARKERS)
        or "/postcards/" in text
    )


# ---------------------------------------------------------------------------
# ML Serializers
# ---------------------------------------------------------------------------
class MLInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLInsight
        fields = ["id", "destination", "insight_type", "label", "score", "raw_result", "created_at"]


class MLResultSerializer(serializers.Serializer):
    insight_type = serializers.CharField()
    label = serializers.CharField(required=False, allow_blank=True)
    score = serializers.FloatField(required=False)
    raw_result = serializers.DictField(required=False)


class MLRecommendationRequestSerializer(serializers.Serializer):
    latitude = CoordinateField(required=False, allow_null=True)
    longitude = CoordinateField(required=False, allow_null=True)
    top_n = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)
    interest = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    province = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    budget = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    travel_style = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    difficulty = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class MLRecommendationResponseSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    name = serializers.CharField()
    score = serializers.FloatField()
    reason = serializers.CharField(required=False, allow_blank=True)


class MLWebhookResultSerializer(serializers.Serializer):
    insight_type = serializers.CharField()
    label = serializers.CharField(required=False, allow_blank=True)
    score = serializers.FloatField(required=False)
    raw_result = serializers.DictField(required=False)
    destination_id = serializers.IntegerField(required=False)


class SafetyPredictionRequestSerializer(serializers.Serializer):
    """
    Either pass latitude/longitude directly, OR a destination id (in which
    case its coordinates/city/country are used automatically).
    """

    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all(), required=False)
    latitude = CoordinateField(required=False)
    longitude = CoordinateField(required=False)

    def validate(self, attrs):
        if "destination" not in attrs and ("latitude" not in attrs or "longitude" not in attrs):
            raise serializers.ValidationError("Provide either `destination` or both `latitude` and `longitude`.")
        return attrs


class SafetyPredictionResponseSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    risk_level = serializers.CharField()
    score = serializers.FloatField()
    factors = serializers.DictField(required=False)


class BudgetPredictionRequestSerializer(serializers.Serializer):
    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all(), required=False)
    city = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    days = serializers.IntegerField(default=3, min_value=1, max_value=90)
    travelers = serializers.IntegerField(default=1, min_value=1, max_value=20)
    budget_level = serializers.ChoiceField(choices=["budget", "mid", "luxury"], default="mid")
    # Traveler's current GPS position -- optional, makes the estimate
    # genuinely distance-aware instead of a flat per-city number.
    user_latitude = serializers.FloatField(required=False, allow_null=True)
    user_longitude = serializers.FloatField(required=False, allow_null=True)
    # Official-fee context (visa / park / TIMS / permits use nationality-
    # specific published rates; seasonal permits need the travel month).
    nationality = serializers.ChoiceField(choices=["foreign", "saarc", "chinese", "nepali"], default="foreign")
    travel_month = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=12)
    include_visa = serializers.BooleanField(default=True)

    def validate(self, attrs):
        destination = attrs.get("destination")
        city = (attrs.get("city") or "").strip()
        if not destination and not city:
            raise serializers.ValidationError({
                "destination": "Please select a destination before estimating a budget. "
                                "Budget estimates are place-specific and can't be generated "
                                "from trip length or traveler count alone."
            })
        return attrs


class BudgetPredictionResponseSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    estimated_budget = serializers.FloatField()
    currency = serializers.CharField()
    breakdown = serializers.DictField(required=False)


class BestRouteRequestSerializer(serializers.Serializer):
    """
    Either pass `destination` as the end point (its coordinates are used
    automatically) or `end_latitude`/`end_longitude` directly. The start
    point is always explicit — it's wherever the tourist currently is.
    """

    start_latitude = CoordinateField(min_value=Decimal("-90"), max_value=Decimal("90"))
    start_longitude = CoordinateField(min_value=Decimal("-180"), max_value=Decimal("180"))
    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all(), required=False)
    end_latitude = CoordinateField(required=False)
    end_longitude = CoordinateField(required=False)

    def validate(self, attrs):
        if "destination" not in attrs and ("end_latitude" not in attrs or "end_longitude" not in attrs):
            raise serializers.ValidationError("Provide either `destination` or both `end_latitude` and `end_longitude`.")
        return attrs


class BestRouteResponseSerializer(serializers.Serializer):
    origin_id = serializers.IntegerField()
    destination_id = serializers.IntegerField()
    distance_km = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    mode = serializers.CharField()
    steps = serializers.ListField(required=False)


class ItineraryRequestSerializer(serializers.Serializer):
    """
    Rich, dataset-driven itinerary builder request. Sent when the
    traveller presses "Generate"; nationality / travel_month drive the
    official permit, fee and visa checks in the trip-readiness section.
    """

    nationality = serializers.ChoiceField(choices=["foreign", "saarc", "chinese", "nepali"], default="foreign")
    travel_month = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=12)
    days = serializers.IntegerField(default=3, min_value=1, max_value=30)
    travelers = serializers.IntegerField(default=1, min_value=1, max_value=50)
    budget_npr = serializers.FloatField(required=False, allow_null=True, min_value=0)
    budget_level = serializers.ChoiceField(
        choices=["budget", "mid", "standard", "luxury"], default="mid"
    )
    travel_style = serializers.ChoiceField(
        choices=["leisure", "adventure", "culture", "nature", "city"], default="leisure"
    )
    travel_type = serializers.ChoiceField(
        choices=["solo", "couple", "family", "group"], default="solo"
    )
    interests = serializers.ListField(
        child=serializers.CharField(max_length=40),
        required=False,
        default=["culture"],
    )

    # Optional scalars a cached or older frontend bundle may still send as a
    # blank string ("Not decided" for the month, an empty budget box). A blank
    # string carries no answer, so it must fall back to the field default
    # instead of failing the whole plan with 400.
    _BLANK_AS_UNSET = (
        "nationality",
        "days",
        "travelers",
        "budget_npr",
        "budget_level",
        "travel_style",
        "travel_type",
        "travel_month",
    )

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        for key in self._BLANK_AS_UNSET:
            value = data.get(key)
            if isinstance(value, str) and not value.strip():
                data.pop(key, None)
        raw_budget = data.get("budget_npr")
        if raw_budget is not None:
            if isinstance(raw_budget, str):
                cleaned = "".join(c for c in raw_budget if c.isdigit() or c == ".")
                if cleaned:
                    try:
                        data["budget_npr"] = float(cleaned)
                    except ValueError:
                        data["budget_npr"] = None
                else:
                    data["budget_npr"] = None
        return super().to_internal_value(data)
    start_city = serializers.CharField(required=False, allow_blank=True, default="Kathmandu")
    # ItineraryView scopes the plan with `district or start_city`; without the
    # key declared here DRF silently drops it and the scope always falls back
    # to the city string.
    district = serializers.CharField(required=False, allow_blank=True, default="")


class ItineraryResponseSerializer(serializers.Serializer):
    days = serializers.ListField()
    total_distance_km = serializers.FloatField(required=False)
    estimated_budget = serializers.FloatField(required=False)


# ---------------------------------------------------------------------------
# Navigation Serializers
# ---------------------------------------------------------------------------
class MLRouteSegmentSerializer(serializers.Serializer):
    start_lat = serializers.FloatField()
    start_lng = serializers.FloatField()
    end_lat = serializers.FloatField()
    end_lng = serializers.FloatField()
    distance_m = serializers.FloatField()
    duration_s = serializers.FloatField()
    instruction = serializers.CharField(required=False, allow_blank=True)


class RouteResponseSerializer(serializers.Serializer):
    distance_m = serializers.FloatField()
    duration_s = serializers.FloatField()
    segments = serializers.ListField(child=MLRouteSegmentSerializer())
    polyline = serializers.CharField(required=False, allow_blank=True)


class DataReportSerializer(serializers.Serializer):
    report_type = serializers.CharField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    data = serializers.DictField(required=False)


class UserRouteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.IntegerField()
    start_latitude = serializers.FloatField()
    start_longitude = serializers.FloatField()
    end_latitude = serializers.FloatField()
    end_longitude = serializers.FloatField()
    distance_km = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    transport_mode = serializers.CharField()
    created_at = serializers.DateTimeField()


# ---------------------------------------------------------------------------
# Emergency directory serializers (restored: commit 7385622 dropped them
# while leaving their importers behind -- every hospital/police payload and
# the media-gallery provenance checks below were raising ImportError).
# ---------------------------------------------------------------------------



class HospitalSerializer(UsablePhoneMixin, serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    hours = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = ["id", "name", "address", "phone", "latitude", "longitude", "district", "image_url", "opening_hours", "hours", "emergency_available", "source_name", "source_url", "is_verified", "verified_at", "updated_at"]

    def get_hours(self, obj):
        from .opening_hours import status as hours_status
        return hours_status(obj.opening_hours)

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        try:
            return public_media_url(obj.image.url, request)
        except (ValueError, AttributeError):
            return None


class PoliceStationSerializer(UsablePhoneMixin, serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PoliceStation
        fields = ["id", "name", "address", "phone", "latitude", "longitude", "image_url", "opening_hours", "emergency_available", "source_name", "source_url", "is_verified", "verified_at", "updated_at"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        try:
            return public_media_url(obj.image.url, request)
        except (ValueError, AttributeError):
            return None


# ---------------------------------------------------------------------------
# Destination photo provenance
#
# is_destination_specific_image() is imported by media_review.py and the
# gallery endpoint, public_destination_cover() by restaurant.py and the AI
# image service, and verified_destination_photos() by the data-quality audit
# command -- all of them broke the moment these definitions disappeared.
# ---------------------------------------------------------------------------

_WIKIMEDIA_HOST = "upload.wikimedia.org"

_IMAGE_STOPWORDS = {
    "the", "and", "for", "view", "views", "photo", "photos", "with", "from",
    "lake", "park", "temple", "stupa", "mountain", "national", "area",
    "valley", "museum", "city", "nepal", "tourism", "hotel", "lodge",
    "resort", "guest", "house", "homestay", "cafe", "restaurant", "point",
    "top", "peak", "hill", "road", "street", "bridge", "gate", "door",
    "wall", "statue", "monument", "memorial", "shrine", "mandir", "basti",
    "chowk", "chaur", "toll", "border", "check", "post", "jpg", "jpeg",
    "png", "gif", "webp", "file", "image",
}

BUNDLED_PLACEHOLDER_MARKERS = (
    "bundled with app",
    "bundled asset",
    "bundled placeholder",
    "generated for nepal",
    "generated for nepal tourism",
    "royalty-free placeholder",
    "placeholder image",
)

BUNDLED_ASSET_PREFIXES = (
    "/images/destinations/",
    "/images/generic/",
    "/images/placeholders/",
    "/static/images/destinations/",
)


def _destination_identity_tokens(destination):
    text = " ".join(filter(None, [
        destination.name,
        getattr(destination, "aliases", "") or "",
        destination.city,
        destination.district,
        getattr(destination, "municipality", "") or "",
        destination.province,
    ])).lower()
    return {t for t in re.findall(r"[a-z0-9]{4,}", text) if t not in _IMAGE_STOPWORDS}


def _named_external_photo_title(url):
    """Descriptive title of a named external photo (Wikimedia), or None.

    Opaque/hash-based URLs carry no verifiable title and keep the legacy
    lenient treatment — we only make strong claims for named sources."""
    try:
        from urllib.parse import unquote, urlparse

        parts = urlparse(str(url or ""))
    except Exception:
        return None
    if _WIKIMEDIA_HOST not in (parts.netloc or ""):
        return None
    path = unquote(parts.path)
    if not path:
        return None
    fn = path.split("/thumb/")[-1].split("/")[-1] if "/thumb/" in path else path.split("/")[-1]
    fn = re.sub(r"^\d+px-", "", fn)
    fn = re.sub(r"\.\w+$", "", fn)
    return fn or None


def image_url_matches_destination(destination, url):
    """Strong-evidence check for named external photos.

    Import-era data assigned many photos of UNRELATED places (a vintage
    phone photo for a consultancy, a monastery pool for a homestay...).
    Wikimedia filenames are descriptive titles, so the match is verifiable
    from the URL itself: the photo title must share a place token with the
    destination's name/aliases/city/district/municipality.

      True  — verified match, safe to display
      False — strong mismatch evidence; never display as this destination
      None  — opaque URL, not verifiable (legacy lenient behaviour)
    """
    title = _named_external_photo_title(url)
    if title is None:
        return None
    tl = title.lower()
    for candidate in filter(None, [
        destination.name,
        destination.city,
        destination.district,
        getattr(destination, "municipality", "") or "",
    ]):
        c2 = str(candidate).lower().strip()
        if len(c2) >= 5 and (c2 in tl or tl in c2):
            return True
    for alias in filter(None, [
        a.strip() for a in (getattr(destination, "aliases", "") or "").split(",")
    ]):
        a2 = alias.lower().strip(" ()")
        if len(a2) >= 4 and a2 in tl:
            return True
    title_tokens = {t for t in re.findall(r"[a-z0-9]{4,}", tl) if t not in _IMAGE_STOPWORDS}
    return bool(title_tokens & _destination_identity_tokens(destination))


def _is_bundled_placeholder_asset(photo, external_url, image_path, source_url):
    """True when this row is a bundled stock asset, not real photography.

    The catalogue shipped a folder of generic images (``temple.jpg``,
    ``tea-gardens.jpg``, ``interior.jpg``) and wired them in as a destination's
    photograph whenever a place had no real image. A traveller searching for a
    place then saw a stock interior and reasonably concluded the catalogue was
    showing a different location. A bundled placeholder is not a wrong place
    exactly - it is not a photograph at all - so it must never be presented as
    this destination's photography. The same rule already applied to generated
    postcards, which render as an honest "no real photo yet" state.
    """
    for candidate in (external_url, image_path, source_url):
        if not candidate:
            continue
        low = str(candidate).lower()
        if is_generated_postcard_url(low):
            return True
        if low.startswith(BUNDLED_ASSET_PREFIXES):
            return True

    provenance = " ".join(filter(None, [
        getattr(photo, "license_type", "") or "",
        getattr(photo, "attribution", "") or "",
        getattr(photo, "photographer", "") or "",
        getattr(photo, "source", "") or "",
    ])).lower()
    return any(marker in provenance for marker in BUNDLED_PLACEHOLDER_MARKERS)


def is_destination_specific_image(destination, photo):
    """Keep destination-linked media unless there is strong mismatch evidence.

    Verification controls trust badges and admin review, not basic visibility.
    This restores generated/imported media while still blocking obvious cases
    such as a Kathmandu photo assigned to Phewa Lake or crash/news imagery.
    """
    import re
    ignored = {"lake", "park", "temple", "stupa", "mountain", "national", "area", "view", "valley", "museum", "city", "nepal", "the", "and", "tourism"}
    destination_text = " ".join(filter(None, [
        destination.name, destination.aliases, destination.city, destination.district, destination.province,
    ])).lower()
    allowed = {token for token in re.findall(r"[a-z0-9]+", destination_text) if len(token) >= 4 and token not in ignored}
    external_url = getattr(photo, "external_url", "") or ""
    local_image = str(getattr(photo, "image", "") or "")
    image_path = getattr(photo, "image_path", "") or ""
    evidence = " ".join([external_url, local_image, image_path, getattr(photo, "source_url", "") or ""]).lower()
    if any(term in evidence for term in ["airlines_crash", "plane_crash", "accident_scene", "placeholder", "stock-photo"]):
        return False
    # A bundled stock asset is not a photograph of this place.
    if _is_bundled_placeholder_asset(photo, external_url, image_path,
                                    getattr(photo, "source_url", "") or ""):
        return False
    # A locally uploaded/generated file is explicitly attached by destination_id.
    if (local_image or image_path) and not external_url:
        return True
    # An admin picked this photo for this destination (media library upload,
    # "add external image", replace-cover) and approved it. The filename
    # heuristics below exist to catch bulk-imported mismatches; they must not
    # silently hide a deliberate admin choice such as
    # https://cdn.example.com/IMG_2041.jpg — that was the "saved in the
    # database but never shown on the public site" bug.
    # ``source == ADMIN`` alone is not enough — it is the model default and
    # automated image searches store it too — so the photo must also have
    # been added by a staff account through the admin UI.
    uploader = getattr(photo, "uploaded_by", None) if getattr(photo, "uploaded_by_id", None) else None
    if (
        getattr(photo, "source", "") == DestinationImage.Source.ADMIN
        and uploader is not None
        and (uploader.is_staff or uploader.is_superuser)
    ):
        return True
    # Named external photos (e.g. Wikimedia titles) can be verified from the
    # URL: a title that shares no place token with this destination is strong
    # mismatch evidence and must not be displayed as its imagery.
    for candidate_url in (external_url, getattr(photo, "source_url", "") or ""):
        if image_url_matches_destination(destination, candidate_url) is False:
            return False
    own_match = any(token in evidence for token in allowed)
    strict_subject = any(term in destination_text for term in ["cave", "gupha", "gufa", "balloon", "ultralight", "paragliding", "zipflyer", "zip flyer"])
    if strict_subject and not own_match:
        return False
    known_places = {"kathmandu", "patan", "bhaktapur", "pokhara", "rara", "lumbini", "mustang", "chitwan", "janakpur", "everest", "annapurna", "tilicho", "gosaikunda", "bardiya", "ilam", "dhangadhi", "dadeldhura", "pashupatinath", "boudhanath", "swayambhunath"}
    conflicts = {place for place in known_places if place in evidence and place not in allowed}
    if conflicts and not own_match:
        return False
    # Unknown/hash-based URLs remain visible only as a fallback. They are
    # never promoted over an exact verified place match.
    return True


def verified_destination_photos(destination):
    """Public galleries show APPROVED photos only.

    Pending uploads (staff/community) stay in the moderation queue and must
    never appear publicly before an admin approves them; rejected never."""
    return [
        photo for photo in destination.gallery.all()
        if photo.verification_status == DestinationImage.ImageStatus.APPROVED
        and photo.is_verified
        and is_destination_specific_image(destination, photo)
    ]


def public_destination_cover(destination, request=None):
    """Return only an approved, verified gallery cover."""
    photos = verified_destination_photos(destination)
    cover = next((photo for photo in photos if photo.is_cover), None) or (photos[0] if photos else None)
    if not cover:
        return None
    if cover.image_path:
        return image_server_url(cover.image_path)
    if cover.external_url:
        return cover.external_url
    if cover.image:
        try:
            return resolve_image_url(cover.image, request)
        except (ValueError, AttributeError):
            return None
    return None


def real_photo_url(photo, request=None):
    """Resolve a verified photo to a display URL, or None when the media is
    a generated postcard or carries no usable file."""
    url = None
    if photo.image_path:
        url = image_server_url(photo.image_path)
    elif photo.external_url:
        url = photo.external_url
    elif photo.image:
        url = resolve_image_url(photo.image, request)
    if url and is_generated_postcard_url(url):
        return None
    return url or None


def resolve_authentic_destination_image(obj):
    """No cross-destination fallback: missing verified media stays unavailable."""
    return None
