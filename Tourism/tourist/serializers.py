from django.contrib.auth import password_validation
from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import (
    User,
    Language,
    Category,
    Destination,
    DestinationTranslation,
    DestinationImage,
    DestinationVideo,
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
)
from .image_server import image_server_url
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


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class UpdateLocationSerializer(serializers.Serializer):
    """Used by the browser-GPS endpoint; falls back to GeoIP server-side if omitted."""

    latitude = CoordinateField(required=False, allow_null=True)
    longitude = CoordinateField(required=False, allow_null=True)


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
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
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


class DestinationTransitRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationTransitRoute
        fields = [
            "id", "destination", "origin", "transport_mode", "distance_km", "approx_duration",
            "road_condition", "key_stops", "estimated_fare_npr", "route_source", "operator_name",
            "contact_phone", "booking_url", "departure_schedule", "is_active", "is_verified", "updated_at"
        ]
        read_only_fields = ["is_verified", "updated_at"]


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
            staff = user.is_staff or user.role in {"admin", "super_admin", "tourism_admin"}
            validated_data["verification_status"] = "approved" if staff else "pending"
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
        if obj.image:
            request = self.context.get("request")
            try:
                return request.build_absolute_uri(obj.image.url) if request else obj.image.url
            except (ValueError, AttributeError):
                pass
        medical = [
            "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1200&q=80",
            "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=1200&q=80",
            "https://images.unsplash.com/photo-1551076805-e1869033e561?w=1200&q=80",
            "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=1200&q=80",
        ]
        return medical[(obj.id or 0) % len(medical)]


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
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
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
        result = None
        if obj.destination:
            if obj.destination.cover_image:
                result = resolve_image_url(obj.destination.cover_image)
            else:
                photos = list(obj.destination.gallery.all())
                approved = [photo for photo in photos if photo.verification_status in {"approved", "verified"}]
                candidates = approved or [photo for photo in photos if photo.verification_status != "rejected"]
                candidates.sort(key=lambda photo: (not photo.is_cover, photo.ordering, photo.id))
                if candidates:
                    photo = candidates[0]
                    result = photo.external_url or resolve_image_url(photo.image)
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
    return [
        photo for photo in destination.gallery.all()
        if photo.verification_status != DestinationImage.ImageStatus.REJECTED
        and is_destination_specific_image(destination, photo)
    ]


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

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "category", "category_name", "short_description",
            "latitude", "longitude", "city", "country", "district", "province", "municipality", "ward_number", "type",
            "average_rating", "ratings_count", "views_count", "entry_fee", "source",
            "cover_image_url", "distance_km", "status", "is_user_submitted", "is_active",
            "budget_estimate", "risk_level", "recommended_season", "gallery_preview", "created_at", "updated_at",
        ]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_budget_estimate(self, obj):
        if hasattr(obj, "budget_estimation") and obj.budget_estimation:
            return float(obj.budget_estimation.estimated_daily_budget or obj.budget_estimation.estimated_trip_budget or 45)
        if obj.entry_fee:
            return float(obj.entry_fee)
        return 35.0

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_risk_level(self, obj):
        if hasattr(obj, "risk_analysis") and obj.risk_analysis:
            return (obj.risk_analysis.risk_category or "low").lower()
        return "low"

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_recommended_season(self, obj):
        return obj.best_time_to_visit or "Sep - Nov / Mar - May"

    def get_gallery_preview(self, obj):
        request = self.context.get("request")
        items = []
        for photo in verified_destination_photos(obj)[:5]:
            if photo.image_path:
                url = image_server_url(photo.image_path)
            elif photo.external_url:
                url = photo.external_url
            elif photo.image:
                url = resolve_image_url(photo.image, request)
            else:
                continue
            items.append({
                "id": photo.id, "url": url, "caption": photo.caption or obj.name,
                "source": photo.source, "source_url": photo.source_url,
                "photographer": photo.photographer, "license": photo.license_type,
                "verification_status": photo.verification_status,
            })
        return items

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        # cover_image is an ImageField, but a large amount of seed data
        # stored external http(s) URLs in it. resolve_image_url returns
        # those verbatim instead of producing broken /media/https%3A/...
        if obj.cover_image:
            return resolve_image_url(obj.cover_image, request)
        photos = verified_destination_photos(obj)
        cover = next((photo for photo in photos if photo.is_cover), None) or (photos[0] if photos else None)
        if cover:
            if cover.image_path:
                return image_server_url(cover.image_path)
            if cover.external_url:
                return cover.external_url
            if cover.image:
                return resolve_image_url(cover.image, request)
        return None

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
    cover_image_url = serializers.SerializerMethodField()
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
    hospitals = HospitalSerializer(many=True, read_only=True)
    police_stations = PoliceStationSerializer(many=True, read_only=True)
    hotels = HotelSerializer(many=True, read_only=True)
    restaurants = serializers.SerializerMethodField()
    sources = DestinationSourceSerializer(many=True, read_only=True)
    activities = DestinationActivitySerializer(many=True, read_only=True)
    attractions = DestinationAttractionSerializer(many=True, read_only=True)
    transit_routes = DestinationTransitRouteSerializer(many=True, read_only=True)
    nearby_places = DestinationNearbyPlaceSerializer(many=True, read_only=True)
    notices = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "aliases", "category", "category_name", "description", "short_description",
            "history", "cultural_significance", "religious_significance", "tourism_importance",
            "food_cuisine_info", "travel_safety_tips", "best_time_to_visit", "altitude",
            "distance_from_kathmandu_km", "distance_from_nearest_city_km", "nearest_major_city",
            "distance_from_nearest_airport_km", "nearest_airport_name", "approx_travel_time", "recommended_days",
            "nearest_hospital_info", "nearest_hotel_info", "nearest_police_info", "district", "municipality",
            "ward_number", "province", "cover_image_url", "latitude", "longitude", "address", "city",
            "country", "opening_hours", "entry_fee", "contact_phone", "contact_email", "website",
            "average_rating", "ratings_count", "views_count", "created_by", "created_by_name",
            "created_by_email", "is_user_submitted", "status", "research_status", "review_note",
            "is_active", "is_featured", "created_at", "updated_at", "images", "gallery", "videos", "reviews", "translations",
            "distance_km", "budget_estimation", "risk_analysis", "hospitals", "police_stations", "hotels", "restaurants",
            "sources", "activities", "attractions", "transit_routes", "nearby_places", "notices",
        ]
        read_only_fields = [
            "slug", "average_rating", "ratings_count", "views_count", "created_by",
            "is_user_submitted", "status", "review_note", "created_at", "updated_at",
        ]

    def get_notices(self, obj):
        from .notices import notices_for_destination, serialize_notice
        return [serialize_notice(notice) for notice in notices_for_destination(obj)[:12]]

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
        request = self.context.get("request")
        # cover_image is an ImageField, but a large amount of seed data
        # stored external http(s) URLs in it. resolve_image_url returns
        # those verbatim instead of producing broken /media/https%3A/...
        if obj.cover_image:
            return resolve_image_url(obj.cover_image, request)
        photos = verified_destination_photos(obj)
        cover = next((photo for photo in photos if photo.is_cover), None) or (photos[0] if photos else None)
        if cover:
            if cover.image_path:
                return image_server_url(cover.image_path)
            if cover.external_url:
                return cover.external_url
            if cover.image:
                return resolve_image_url(cover.image, request)
        return None

    def get_gallery(self, obj):
        photos = verified_destination_photos(obj)
        return DestinationImageSerializer(photos, many=True, context=self.context).data

    @extend_schema_field(serializers.ListField(child=serializers.URLField(), allow_empty=True))
    def get_images(self, obj):
        """Ordered list of absolute image URLs (standalone image server first, then other sources)."""
        urls = []
        seen = set()
        for photo in verified_destination_photos(obj):
            url = None
            if photo.image_path:
                url = image_server_url(photo.image_path)
            elif photo.image:
                request = self.context.get("request")
                url = request.build_absolute_uri(photo.image.url) if request else photo.image.url
            else:
                url = photo.external_url
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
    latitude = CoordinateField(required=False, allow_null=True)
    longitude = CoordinateField(required=False, allow_null=True)

    class Meta:
        model = Destination
        fields = [
            "id", "name", "category", "description", "short_description", "cover_image",
            "latitude", "longitude", "address", "city", "district", "municipality", "ward_number",
            "province", "country", "altitude", "opening_hours", "best_time_to_visit", "history",
            "nearest_hospital_info", "nearest_hotel_info", "nearest_police_info",
            "entry_fee", "contact_phone", "contact_email", "website", "is_active",
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
        if user.is_staff:
            # Staff-created destinations are published immediately.
            validated_data["is_user_submitted"] = False
            validated_data["status"] = Destination.SubmissionStatus.APPROVED
        else:
            # Tourist submissions wait for admin approval before going live.
            validated_data["is_user_submitted"] = True
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
    latitude = CoordinateField()
    longitude = CoordinateField()
    radius_km = serializers.FloatField(default=10, min_value=0.1, max_value=500)


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

    start_latitude = CoordinateField()
    start_longitude = CoordinateField()
    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all(), required=False)
    end_latitude = CoordinateField(required=False)
    end_longitude = CoordinateField(required=False)

    def validate(self, attrs):
        if "destination" not in attrs and ("end_latitude" not in attrs or "end_longitude" not in attrs):
            raise serializers.ValidationError("Provide either `destination` or both `end_latitude` and `end_longitude`.")
        return attrs


class ItineraryRequestSerializer(serializers.Serializer):
    """
    Rich, dataset-driven itinerary builder request. Every field feeds the
    ML service's /itinerary/build endpoint so the plan (destinations,
    budget in NPR, route legs from the road graph) updates continuously as
    the user changes any input.
    """

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
    start_city = serializers.CharField(required=False, allow_blank=True, default="Kathmandu")


class OSMEssentialServiceSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OSMEssentialService
        fields = ["id", "osm_id", "category", "name", "phone", "latitude", "longitude", "address", "image_url", "opening_hours", "emergency_available", "source_name", "source_url", "is_verified", "verified_at", "created_at", "updated_at"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        try:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        except (ValueError, AttributeError):
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
