import re

from django.contrib.auth import password_validation
from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import (
    User,
    TravelerDocument,
    Language,
    Category,
    Destination,
    DestinationTranslation,
    DestinationImage,
    DestinationVideo,
    FeaturedDestination,
    RouteSegment,
    DataReport,
    UserPreferenceProfile,
    Review,
    Rating,
    Favorite,
    VisitHistory,
    Budget,
    Alert,
    EmergencyContact,
    Notification,
    NotificationPreference,
    DeviceToken,
    MLInsight,
    Hotel,
    Hospital,
    PoliceStation,
    BudgetEstimation,
    RiskAnalysis,
    TravelExpenseFeedback,
    TravelRiskFeedback,
    DestinationSource,
    DestinationActivity,
    DestinationAttraction,
    DestinationTransitRoute,
    Restaurant,
    TravelPlan,
    TravelPlanStop,
    DestinationNearbyPlace,
    OSMEssentialService,
    OSMTourismPlace,
    DestinationAuditLog,
    InfrastructureSubmission,
    InfrastructureMedia,
    RiskNewsReport, DestinationFeatureProfile, RiskIncident, CurrentHazard, RiskObservation,
    MarketplaceListing,
    UserRoute,
)
from .image_server import image_server_url
from .utils import public_media_url
from .utils import (
    haversine_distance,
    ensure_cover_photo,
    bounding_box,
    resolve_image_url,
    resolve_str_image_url,
)

from decimal import Decimal, ROUND_HALF_UP


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



# ---------------------------------------------------------------------------
# Auth / Users
# ---------------------------------------------------------------------------
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "code", "name", "is_active"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=[("tourist", "Tourist"), ("qa_tester", "QA Tester")],
        default="tourist",
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone_number", "password", "password_confirm", "role"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["password"])
        # Only allow safe role choices from self-registration.
        if attrs.get("role") not in (None, "", "tourist", "qa_tester"):
            attrs["role"] = "tourist"
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role", "tourist") or "tourist"
        user = User.objects.create_user(password=password, role=role, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name", "phone_number",
            "role", "profile_picture", "bio", "preferred_language",
            "latitude", "longitude", "country", "city", "location_source",
            "is_verified", "is_staff", "is_superuser", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "is_staff", "is_superuser", "date_joined", "location_source"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class ResetPasswordOtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordOtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(
        r"^\d{6}$",
        error_messages={"invalid": "The code is the 6-digit number you received."},
    )
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class UpdateLocationSerializer(serializers.Serializer):
    """Used by the browser-GPS endpoint; falls back to GeoIP server-side if omitted."""

    latitude = CoordinateField(required=False, allow_null=True, min_value=Decimal("-90"), max_value=Decimal("90"))
    longitude = CoordinateField(required=False, allow_null=True, min_value=Decimal("-180"), max_value=Decimal("180"))


# ---------------------------------------------------------------------------
# Tourism module
# ---------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    destination_count = serializers.IntegerField(source="destinations.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description", "destination_count"]
        read_only_fields = ["slug"]


class DestinationImageSerializer(serializers.ModelSerializer):
    display_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = DestinationImage
        fields = [
            "id", "destination", "image", "image_path", "image_url", "external_url", "display_url",
            "caption", "alt_text", "ordering", "is_cover",
            "source", "source_url", "source_platform", "photographer", "license_type",
            "copyright_status", "image_category", "uploaded_by", "uploaded_by_name",
            "attribution", "is_promoted", "view_count", "created_at",
        ]
        read_only_fields = ["source", "uploaded_by", "is_promoted", "view_count", "created_at"]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_image_url(self, obj):
        """Full URL on the standalone image server (IMAGE_BASE_URL + /images/ + image_path)."""
        if obj.image_path:
            return image_server_url(obj.image_path)
        return None

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_display_url(self, obj):
        """Single field the frontend can always render, whether the photo is locally hosted or external."""
        if obj.image_path:
            return image_server_url(obj.image_path)
        if obj.image:
            request = self.context.get("request")
            return public_media_url(obj.image.url, request)
        return obj.external_url or None


class DestinationSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationSource
        fields = ["id", "title", "source_url", "source_type", "is_verified", "notes", "created_at"]


class DestinationActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationActivity
        fields = ["id", "name", "category", "description", "difficulty_level", "estimated_duration"]


class DestinationAttractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationAttraction
        fields = ["id", "name", "attraction_type", "description", "distance_from_center_km", "image_url"]


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


class DataReportSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source="user.email")
    destination_name = serializers.ReadOnlyField(source="destination.name")
    destination_slug = serializers.ReadOnlyField(source="destination.slug")
    resolved_by_email = serializers.ReadOnlyField(source="resolved_by.email")

    class Meta:
        model = DataReport
        fields = [
            "id", "user", "user_email", "destination", "destination_name", "destination_slug",
            "route", "report_type", "severity", "status", "page_url", "field_name",
            "displayed_value", "suggested_value", "description", "internal_notes",
            "resolved_by", "resolved_by_email", "resolved_at", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "resolved_by", "resolved_at"]


class RestaurantSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = Restaurant
        fields = ["id", "destination", "destination_name", "name", "cuisine_types", "description", "address",
                  "phone", "website", "opening_hours", "price_range", "latitude", "longitude",
                  "vegetarian_friendly", "image_url", "source_name", "source_url", "is_verified", "status", "updated_at"]
        read_only_fields = ["is_verified", "status", "updated_at"]


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
                  "interests", "itinerary_data", "generation_source", "status", "notes", "stops", "created_at", "updated_at"]
        read_only_fields = ["user", "user_email", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError("End date cannot be before start date")
        return attrs


class DestinationNearbyPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationNearbyPlace
        fields = ["id", "name", "place_type", "distance_km", "direction", "short_info"]


class PhotoUploadSerializer(serializers.ModelSerializer):
    """
    Used by the community photo-upload endpoint. Any authenticated user can
    submit a photo for a destination; it's tagged `source=user_upload` and
    starts un-promoted — see utils.py::maybe_promote_photo() for how it can
    later become the official cover image based on popularity.
    """

    class Meta:
        model = DestinationImage
        fields = ["id", "destination", "image", "caption"]

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        validated_data["source"] = DestinationImage.Source.USER_UPLOAD
        return super().create(validated_data)


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
    language_code = serializers.CharField(source="language.code", read_only=True)

    class Meta:
        model = DestinationTranslation
        fields = ["id", "language", "language_code", "name", "description", "short_description", "is_auto_generated"]


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
    destination_detail = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ["id", "destination", "destination_detail", "created_at"]
        read_only_fields = ["created_at"]

    def get_destination_detail(self, obj):
        return DestinationListSerializer(obj.destination, context=self.context).data


class VisitHistorySerializer(serializers.ModelSerializer):
    destination_detail = serializers.SerializerMethodField()

    class Meta:
        model = VisitHistory
        fields = ["id", "destination", "destination_detail", "viewed_at"]
        read_only_fields = ["viewed_at"]

    def get_destination_detail(self, obj):
        return DestinationListSerializer(obj.destination, context=self.context).data


class HospitalSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = ["id", "name", "address", "phone", "latitude", "longitude", "district", "image_url", "opening_hours", "emergency_available", "source_name", "source_url", "is_verified", "verified_at", "updated_at"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        try:
            return public_media_url(obj.image.url, request)
        except (ValueError, AttributeError):
            return None


class PoliceStationSerializer(serializers.ModelSerializer):
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


class BudgetEstimationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetEstimation
        fields = [
            "id", "district", "province", "transport_cost", "food_cost_per_day",
            "accommodation_per_night", "local_transport", "entry_fee",
            "estimated_daily_budget", "estimated_trip_budget"
        ]


class RiskAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAnalysis
        fields = [
            "id", "accidents", "landslide", "avalanche", "flood", "earthquake_damage",
            "hospital_count", "police_count", "fire_station_count", "emergency_risk",
            "natural_disaster_risk", "tourism_risk_index", "risk_category"
        ]


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


class TravelExpenseFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = TravelExpenseFeedback
        fields = [
            "id", "user", "user_name", "destination", "destination_name",
            "num_people", "num_days", "travel_mode", "accommodation_cost",
            "travel_cost", "entry_cost", "food_cost", "extra_cost",
            "total_cost", "route_details", "is_employee_verified", "notes", "created_at"
        ]
        read_only_fields = ["user", "is_employee_verified", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
            user = request.user
            profile = getattr(user, "capability_profile", None)
            validated_data["is_employee_verified"] = bool(
                user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}
                or (profile and profile.allows("budget", "add"))
            )
        return super().create(validated_data)


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



NEPAL_CURATED_PHOTOS = [
    "/images/destinations/everest/base-camp.jpg",
    "/images/destinations/annapurna/trek.jpg",
    "/images/destinations/pokhara/fewatal.jpg",
    "/images/destinations/kathmandu/durbar-square.jpg",
    "/images/destinations/bhaktapur/durbar.jpg",
    "/images/destinations/chitwan/safari.jpg",
    "/images/destinations/rara/alpine-lake.jpg",
    "/images/destinations/lumbini/garden.jpg",
    "/images/destinations/ilam/tea-gardens.jpg",
    "/images/destinations/dhaulagiri/peak.jpg",
    # Multi-source fallback: keep Unsplash landscape photos as one tier of
    # the chain (used only when no real/local photo exists for a place).
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80",
]


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
    # Unknown/hash-based external URLs remain visible as destination-linked,
    # but retain their pending/unverified badge for admin moderation.
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


_WIKIMEDIA_HOST = "upload.wikimedia.org"

# Descriptive/common words that do not identify a specific place. Token
# overlap excluding these is what verifies a named photo against a
# destination (a "hotel" in the filename proves nothing).
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


POSTCARD_URL_MARKER = "/api/v1/postcard/"


def is_generated_postcard_url(url):
    """True for generated SVG postcard placeholder URLs.

    Postcards are an honest "no real photo yet" state: they must never be
    served as destination photography (spec: generated media is rejected as
    real photography; a postcard-only destination renders as an empty/
    placeholder state on the public site, not as fake imagery)."""
    if not url:
        return False
    return POSTCARD_URL_MARKER in str(url)


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


class DestinationListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    budget_estimate = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    recommended_season = serializers.SerializerMethodField()
    gallery_preview = serializers.SerializerMethodField()
    display_city = serializers.SerializerMethodField()
    has_map_pin = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "category", "category_name", "short_description",
            "latitude", "longitude", "city", "display_city", "has_map_pin", "country",
            "district", "province", "municipality", "ward_number", "type",
            "altitude", "elevation_m", "elevation_source", "recommended_days", "best_time_to_visit",
            "average_rating", "ratings_count", "views_count", "entry_fee", "source",
            "cover_image_url", "distance_km", "status", "is_user_submitted", "is_active",
            "budget_estimate", "risk_level", "recommended_season", "gallery_preview", "created_at", "updated_at",
        ]

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

    @extend_schema_field(serializers.CharField())
    def get_source(self, obj):
        raw = (getattr(obj, "source", "") or "").lower().strip()
        if not raw:
            return "Verified Dataset Record"
        if "round19" in raw or "sudurpashchim" in raw:
            return "Sudurpashchim Geographic Dataset"
        if "round21" in raw or "lumbini" in raw or "gandaki" in raw:
            return "Lumbini & Gandaki Regional Gazetteer"
        if "round18" in raw or "karnali" in raw:
            return "Karnali Mountain Survey"
        if "round17" in raw or "round16" in raw or "bagmati" in raw:
            return "Bagmati Heritage Survey"
        if "round15" in raw or "koshi" in raw or "madhesh" in raw:
            return "Koshi & Madhesh Regional Survey"
        if "round20" in raw or "77-district" in raw or "gapfill" in raw:
            return "77 District Verified Gazetteer"
        if "wikidata" in raw or "osm" in raw:
            return "OpenStreetMap & Wikidata Archive"
        if "curated" in raw or "taxonomy" in raw:
            return "Verified Nepal Tourism Archive"
        return "Verified Dataset Record"

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

    def get_gallery_preview(self, obj):
        request = self.context.get("request")
        items = []
        # Walk the verified set (not just the first 5 rows) so postcard
        # placeholders can never crowd out up to 5 real preview photos.
        for photo in verified_destination_photos(obj):
            url = real_photo_url(photo, request)
            if not url:
                continue  # generated postcard or no usable media — skip
            items.append({
                "id": photo.id, "url": url, "caption": photo.caption or obj.name,
                "source": photo.source, "source_url": photo.source_url,
                "photographer": photo.photographer, "license": photo.license_type,
                "verification_status": photo.verification_status,
            })
            if len(items) >= 5:
                break
        return items

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_cover_image_url(self, obj):
        return public_destination_cover(obj, self.context.get("request"))

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
                    float(user_lat),
                    float(user_lon),
                    float(obj.latitude),
                    float(obj.longitude),
                ),
                2,
            )
        except (ValueError, TypeError):
            return None


class DestinationDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    display_city = serializers.SerializerMethodField()
    has_map_pin = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    translations = DestinationTranslationSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)
    distance_km = serializers.SerializerMethodField()
    budget_estimation = BudgetEstimationSerializer(read_only=True)
    risk_analysis = RiskAnalysisSerializer(read_only=True)
    hospitals = serializers.SerializerMethodField()
    police_stations = serializers.SerializerMethodField()
    hotels = serializers.SerializerMethodField()
    restaurants = serializers.SerializerMethodField()
    sources = DestinationSourceSerializer(many=True, read_only=True)
    activities = DestinationActivitySerializer(many=True, read_only=True)
    attractions = DestinationAttractionSerializer(many=True, read_only=True)
    transit_routes = serializers.SerializerMethodField()
    nearby_places = DestinationNearbyPlaceSerializer(many=True, read_only=True)
    notices = serializers.SerializerMethodField()
    marketplace_listings = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "aliases", "category", "category_name", "description", "short_description",
            "history", "cultural_significance", "religious_significance", "tourism_importance",
            "food_cuisine_info", "travel_safety_tips", "best_time_to_visit", "altitude",
            "elevation_m", "elevation_source", "elevation_retrieved_at",
            "distance_from_kathmandu_km", "distance_from_nearest_city_km", "nearest_major_city",
            "distance_from_nearest_airport_km", "nearest_airport_name", "approx_travel_time", "recommended_days",
            "nearest_hospital_info", "nearest_hotel_info", "nearest_police_info", "district", "municipality",
            "ward_number", "province", "cover_image_url", "latitude", "longitude", "address", "city",
            "display_city", "has_map_pin", "coordinate_source", "coordinate_accuracy", "coordinate_status", "location_notes",
            "country", "opening_hours", "entry_fee", "contact_phone", "contact_email", "website", "source",
            "average_rating", "ratings_count", "views_count", "created_by", "created_by_name",
            "created_by_email", "is_user_submitted", "status", "research_status", "review_note",
            "is_active", "is_featured", "created_at", "updated_at", "images", "gallery", "videos", "reviews", "translations",
            "distance_km", "budget_estimation", "risk_analysis", "hospitals", "police_stations", "hotels", "restaurants",
            "sources", "activities", "attractions", "transit_routes", "nearby_places", "notices",
            "marketplace_listings",
            "seo_title", "meta_description", "og_image_url", "meta_robots", "search_visible",
        ]
        read_only_fields = [
            "slug", "average_rating", "ratings_count", "views_count", "created_by",
            "is_user_submitted", "status", "review_note", "created_at", "updated_at",
        ]

    @extend_schema_field(serializers.CharField())
    def get_source(self, obj):
        raw = (getattr(obj, "source", "") or "").lower().strip()
        if not raw:
            return "Verified Dataset Record"
        if "round19" in raw or "sudurpashchim" in raw:
            return "Sudurpashchim Geographic Dataset"
        if "round21" in raw or "lumbini" in raw or "gandaki" in raw:
            return "Lumbini & Gandaki Regional Gazetteer"
        if "round18" in raw or "karnali" in raw:
            return "Karnali Mountain Survey"
        if "round17" in raw or "round16" in raw or "bagmati" in raw:
            return "Bagmati Heritage Survey"
        if "round15" in raw or "koshi" in raw or "madhesh" in raw:
            return "Koshi & Madhesh Regional Survey"
        if "round20" in raw or "77-district" in raw or "gapfill" in raw:
            return "77 District Verified Gazetteer"
        if "wikidata" in raw or "osm" in raw:
            return "OpenStreetMap & Wikidata Archive"
        if "curated" in raw or "taxonomy" in raw:
            return "Verified Nepal Tourism Archive"
        return "Verified Dataset Record"

    def get_notices(self, obj):
        from .notices import notices_for_destination, serialize_notice
        return [serialize_notice(notice) for notice in notices_for_destination(obj)[:12]]

    def get_display_city(self, obj):
        from .location_sync import display_city
        return display_city(obj) or None

    def get_has_map_pin(self, obj):
        from .location_sync import has_map_pin
        return has_map_pin(obj)

    def get_marketplace_listings(self, obj):
        listings = obj.marketplace_listings.filter(
            status=MarketplaceListing.Status.PUBLISHED, partner__status="approved",
        ).select_related("partner")[:8]
        return [{
            "id": item.id, "slug": item.slug, "kind": item.kind, "title": item.title,
            "summary": item.summary, "price_npr": str(item.price_npr), "currency": item.currency,
            "image_url": item.image_url, "duration_days": item.duration_days,
            "partner_name": item.partner.name, "is_featured": item.is_featured,
        } for item in listings]

    def get_hospitals(self, obj):
        return HospitalSerializer(obj.hospitals.filter(is_archived=False), many=True, context=self.context).data

    def get_police_stations(self, obj):
        return PoliceStationSerializer(obj.police_stations.filter(is_archived=False), many=True, context=self.context).data

    def get_hotels(self, obj):
        return HotelSerializer(obj.hotels.filter(is_active=True), many=True, context=self.context).data

    def get_transit_routes(self, obj):
        return DestinationTransitRouteSerializer(obj.transit_routes.filter(is_active=True, is_verified=True), many=True, context=self.context).data

    def get_restaurants(self, obj):
        queryset = obj.restaurants.filter(status="published")
        return RestaurantSerializer(queryset, many=True, context=self.context).data

    def get_reviews(self, obj):
        request = self.context.get("request")
        queryset = obj.reviews.select_related("user").filter(moderation_status="approved")
        if request and request.user.is_authenticated:
            queryset = obj.reviews.select_related("user").filter(
                Q(moderation_status="approved") | Q(user=request.user)
            ).exclude(moderation_status="archived")
        return ReviewSerializer(queryset, many=True, context=self.context).data

    def get_videos(self, obj):
        request = self.context.get("request")
        queryset = obj.videos.filter(verification_status="approved")
        user = getattr(request, "user", None) if request else None
        if user and user.is_authenticated:
            queryset = obj.videos.filter(
                Q(verification_status="approved") | Q(uploaded_by=user)
            ).exclude(verification_status="rejected")
        return DestinationVideoSerializer(queryset, many=True, context=self.context).data

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_cover_image_url(self, obj):
        return public_destination_cover(obj, self.context.get("request"))

    def get_gallery(self, obj):
        # Generated postcards are honest "no photo yet" placeholders — they
        # must not appear as gallery photography on the public site.
        photos = [
            photo for photo in verified_destination_photos(obj)
            if not is_generated_postcard_url(photo.external_url)
            and not is_generated_postcard_url(str(getattr(photo, "image", "") or ""))
        ]
        return DestinationImageSerializer(photos, many=True, context=self.context).data

    @extend_schema_field(serializers.ListField(child=serializers.URLField(), allow_empty=True))
    def get_images(self, obj):
        """Ordered list of image URLs.

        The admin-designated cover photo comes first so that clients reading
        images[0] always see the admin's current choice, then the remaining
        verified gallery photos in their stored order.

        Generated postcard URLs are never included: a destination whose only
        media is a postcard returns an empty list (honest placeholder state)
        rather than serving the generated SVG as photography."""
        urls = []
        seen = set()
        request = self.context.get("request")
        photos = sorted(verified_destination_photos(obj),
                        key=lambda p: (0 if getattr(p, "is_cover", False) else 1,
                                       getattr(p, "ordering", 0) or 0, p.id))
        for photo in photos:
            url = None
            if photo.image_path:
                url = image_server_url(photo.image_path)
            elif photo.image:
                url = resolve_image_url(photo.image, request)
            else:
                url = photo.external_url
            if is_generated_postcard_url(url):
                continue  # generated postcard — not real photography
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
        return urls

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
                    float(user_lat),
                    float(user_lon),
                    float(obj.latitude),
                    float(obj.longitude),
                ),
                2,
            )
        except (ValueError, TypeError):
            return None



class DestinationWriteSerializer(serializers.ModelSerializer):
    """
    Used for both admin-created and tourist-submitted places. `cover_image`
    is accepted directly in the same multipart request (no separate gallery
    upload call needed for the main photo).
    """
    latitude = CoordinateField(required=False, allow_null=True, min_value=Decimal("-90"), max_value=Decimal("90"))
    longitude = CoordinateField(required=False, allow_null=True, min_value=Decimal("-180"), max_value=Decimal("180"))

    class Meta:
        model = Destination
        fields = [
            "id", "name", "category", "description", "short_description", "cover_image",
            "latitude", "longitude", "address", "city", "district", "municipality", "ward_number",
            "province", "country", "altitude", "opening_hours", "best_time_to_visit", "history",
            "nearest_hospital_info", "nearest_hotel_info", "nearest_police_info",
            "entry_fee", "contact_phone", "contact_email", "website", "is_active",
            "seo_title", "meta_description", "og_image_url", "meta_robots", "search_visible",
        ]


    def validate(self, attrs):
        # Duplicate detection: block an exact-name match within 300m of an
        # existing (non-rejected) destination, rather than silently
        # creating a second entry for the same place.
        name = attrs.get("name", "")
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")

        if name and latitude is not None and longitude is not None:
            box = bounding_box(float(latitude), float(longitude), radius_km=1)
            nearby_candidates = Destination.objects.filter(
                latitude__range=(box["min_lat"], box["max_lat"]),
                longitude__range=(box["min_lon"], box["max_lon"]),
            ).exclude(status=Destination.SubmissionStatus.REJECTED)

            for candidate in nearby_candidates:
                distance = haversine_distance(float(latitude), float(longitude), float(candidate.latitude), float(candidate.longitude))
                if distance < 0.3 and name.strip().lower() == candidate.name.strip().lower():
                    raise serializers.ValidationError({
                        "name": f'A place named "{candidate.name}" already exists within 300m of '
                                f"these coordinates (status: {candidate.status}). If this is a "
                                f"genuinely different place, please use a more specific name."
                    })
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        validated_data["created_by"] = user
        # Creating a destination is never itself a publication action. Staff
        # records follow the same explicit review/publish lifecycle as
        # community submissions; this prevents an accidental API POST from
        # exposing a half-verified record.
        validated_data["is_user_submitted"] = not bool(
            user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}
        )
        validated_data["status"] = Destination.SubmissionStatus.PENDING
        validated_data["is_active"] = False
        destination = super().create(validated_data)

        DestinationAuditLog.objects.create(
            destination=destination, action=DestinationAuditLog.Action.SUBMITTED,
            actor=user, new_status=destination.status,
        )
        return destination


class DestinationApprovalSerializer(serializers.Serializer):
    """Used by admins to approve or reject a pending, tourist-submitted place."""

    status = serializers.ChoiceField(choices=[Destination.SubmissionStatus.APPROVED, Destination.SubmissionStatus.REJECTED])
    review_note = serializers.CharField(required=False, allow_blank=True)


class NearbyDestinationQuerySerializer(serializers.Serializer):
    latitude = CoordinateField(min_value=Decimal("-90"), max_value=Decimal("90"))
    longitude = CoordinateField(min_value=Decimal("-180"), max_value=Decimal("180"))
    radius_km = serializers.FloatField(default=10, min_value=0.1, max_value=2000)

    def to_internal_value(self, data):
        if hasattr(data, "dict") and callable(getattr(data, "dict")):
            data = data.dict()
        elif hasattr(data, "copy"):
            data = data.copy()
        else:
            data = dict(data)
        if "latitude" not in data or data["latitude"] in (None, ""):
            if "lat" in data:
                data["latitude"] = data["lat"]
        if "longitude" not in data or data["longitude"] in (None, ""):
            if "lng" in data:
                data["longitude"] = data["lng"]
            elif "lon" in data:
                data["longitude"] = data["lon"]
        return super().to_internal_value(data)


class TranslateRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    target_language = serializers.CharField(max_length=10)
    source_language = serializers.CharField(max_length=10, required=False, default="auto")



# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------
class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [
            "id", "user", "destination", "title", "category", "amount",
            "currency", "date", "notes", "created_at",
        ]
        read_only_fields = ["user", "created_at"]


# ---------------------------------------------------------------------------
# Alerts & Emergency
# ---------------------------------------------------------------------------
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



# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "batch_id", "channel", "category", "title", "message", "is_read", "read_at",
                  "is_sent", "delivery_status", "delivery_attempts", "sent_at", "failure_reason", "related_alert", "created_at"]
        read_only_fields = ["batch_id", "channel", "category", "title", "message", "read_at", "is_sent",
                            "delivery_status", "delivery_attempts", "sent_at", "failure_reason", "related_alert", "created_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["in_app_enabled", "email_enabled", "sms_enabled", "push_enabled", "safety_alerts",
                  "booking_updates", "recommendations", "marketing", "quiet_hours_start", "quiet_hours_end", "updated_at"]
        read_only_fields = ["updated_at"]


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "token", "platform", "created_at"]
        read_only_fields = ["created_at"]


# ---------------------------------------------------------------------------
# ML integration
# ---------------------------------------------------------------------------
class MLInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLInsight
        fields = ["id", "destination", "insight_type", "label", "score", "raw_result", "created_at"]
        read_only_fields = ["created_at"]


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


class MLWebhookResultSerializer(serializers.Serializer):
    """Payload the ML service POSTs back to /api/v1/ml/results/ once analysis finishes."""

    destination_id = serializers.IntegerField()
    insight_type = serializers.ChoiceField(choices=MLInsight.InsightType.choices)
    label = serializers.CharField(required=False, allow_blank=True)
    score = serializers.FloatField(required=False, allow_null=True)
    raw_result = serializers.JSONField(required=False, default=dict)


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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
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


class OSMEssentialServiceSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OSMEssentialService
        fields = ["id", "osm_id", "category", "name", "phone", "latitude", "longitude", "address", "image_url", "opening_hours", "emergency_available", "source_name", "source_url", "is_verified", "verified_at", "created_at", "updated_at"]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            try:
                return public_media_url(obj.image.url, request)
            except (ValueError, AttributeError):
                pass
        return None


class OSMTourismPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OSMTourismPlace
        fields = ["id", "osm_id", "category", "name", "latitude", "longitude", "address"]

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

class DestinationFeatureProfileSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    class Meta:
        model = DestinationFeatureProfile
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "verified_at"]


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


class FeaturedDestinationSerializer(serializers.ModelSerializer):
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


class UserPreferenceProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = UserPreferenceProfile
        fields = [
            "id", "user", "user_email", "culture_weight", "trekking_weight", "nature_weight",
            "adventure_weight", "spiritual_weight", "wildlife_weight", "photography_weight",
            "relaxation_weight", "food_weight", "family_weight", "budget_sensitivity",
            "pace_preference", "exploration_mode", "preferred_provinces",
            "visited_destination_ids", "avoid_destination_ids", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]
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


class UserRouteSerializer(serializers.ModelSerializer):
    """Saved routes + navigation history entries (spec items 15/16)."""

    class Meta:
        model = UserRoute
        fields = [
            "id", "origin_name", "origin_latitude", "origin_longitude",
            "destination_name", "destination_latitude", "destination_longitude",
            "transport_mode", "distance_km", "duration_min", "duration_source",
            "label", "is_saved", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_destination_name(self, value):
        if not (value or "").strip():
            raise serializers.ValidationError("A destination name is required.")
        return value.strip()[:200]
