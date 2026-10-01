"""
Common serializer mixins and utilities.
"""
from rest_framework import serializers

from .models import (
    Language, Category, Destination, DestinationImage, DestinationVideo,
    DestinationTranslation, Review, Rating, Favorite, VisitHistory, Budget,
    Alert, EmergencyContact, Notification, NotificationPreference, DeviceToken, Hotel,
    OSMEssentialService, OSMTourismPlace, DestinationAuditLog,
    TravelExpenseFeedback, TravelRiskFeedback, InfrastructureSubmission, InfrastructureMedia,
    CurrentHazard, RiskIncident, RiskObservation, RecommendationEvent, RiskNewsReport,
    SiteSetting, ManagedPage, ContentSection, ManagedNavigationItem, CMSContentTranslation, DestinationFeatureProfile, StaffCapabilityProfile,
    Restaurant, DestinationTransitRoute, TravelPlan, TravelPlanStop, HeroSlide,
    TravelerDocument, RedirectRule, NewsletterSignup, MLInsight,
    FeaturedDestination,
)


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
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "code", "name", "is_active"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description"]


class DestinationListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image = serializers.SerializerMethodField()

    def get_cover_image(self, obj):
        # Imported production data primarily stores reusable remote media in
        # DestinationImage.external_url rather than an ImageField. Expose the
        # actual approved cover URL through the existing frontend contract.
        if getattr(obj, "cover_image", None):
            try:
                return obj.cover_image.url
            except Exception:
                pass
        gallery = getattr(obj, "gallery", None)
        if gallery is not None:
            photo = next(
                (
                    p for p in gallery.all()
                    if getattr(p, "verification_status", "approved") == "approved"
                    and (getattr(p, "is_cover", False) or getattr(p, "external_url", ""))
                ),
                None,
            )
            if photo:
                if getattr(photo, "image_path", ""):
                    from .utils import public_media_url
                    return public_media_url(photo.image_path)
                if getattr(photo, "external_url", ""):
                    return photo.external_url
                if getattr(photo, "image", None):
                    try:
                        return photo.image.url
                    except Exception:
                        pass
        return ""

    class Meta:
        model = Destination
        fields = ["id", "name", "slug", "city", "country", "category_name", "average_rating", "cover_image", "is_featured"]


class DestinationDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Destination
        fields = ["id", "name", "slug", "description", "short_description", "city", "country", "category_name", "average_rating", "ratings_count", "views_count", "cover_image", "latitude", "longitude", "address", "opening_hours", "entry_fee", "is_featured", "is_active", "status", "created_at", "updated_at"]


class DestinationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["name", "description", "short_description", "city", "country", "category", "latitude", "longitude", "address", "opening_hours", "entry_fee"]


class DestinationApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["status", "review_note"]


class DestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationImage
        fields = ["id", "destination", "image", "external_url", "alt_text", "ordering", "is_cover", "source", "verification_status"]


class DestinationVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationVideo
        fields = ["id", "destination", "video_url", "title"]


class DestinationTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationTranslation
        fields = ["id", "destination", "language", "name", "description", "short_description", "is_auto_generated"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "destination", "user", "user_name", "comment", "created_at"]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "destination", "user", "value", "created_at"]


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["id", "user", "destination", "created_at"]


class VisitHistorySerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = VisitHistory
        fields = ["id", "user", "destination", "destination_name", "viewed_at"]


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "user", "destination", "amount", "currency", "start_date", "end_date", "notes"]


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["id", "title", "message", "severity", "is_active", "province", "created_at"]


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ["id", "name", "phone", "type", "province", "district", "is_active"]


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
    limit = serializers.IntegerField(default=20)


class TranslateRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    source_language = serializers.CharField(required=False, default="en")
    target_language = serializers.CharField()


class PhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    destination_id = serializers.IntegerField()
    caption = serializers.CharField(required=False, allow_blank=True)


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ["id", "name", "slug", "description", "city", "country", "price_per_night", "rating", "address", "phone", "email", "website", "latitude", "longitude", "is_active"]


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
    class Meta:
        model = TravelRiskFeedback
        fields = ["id", "user", "destination", "risk_type", "severity", "description", "created_at"]


class InfrastructureSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureSubmission
        fields = ["id", "user", "name", "category", "description", "latitude", "longitude", "status", "created_at"]


class InfrastructureMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureMedia
        fields = ["id", "submission", "image", "media_type", "description"]


class RiskNewsReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskNewsReport
        fields = ["id", "title", "content", "source", "published_at", "is_active"]


class DestinationFeatureProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationFeatureProfile
        fields = ["id", "destination", "features", "created_at", "updated_at"]


class RiskIncidentAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskIncident
        fields = ["id", "title", "description", "severity", "status", "province", "district", "occurred_at", "created_at"]


class CurrentHazardAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentHazard
        fields = ["id", "title", "description", "severity", "province", "district", "expires_at", "is_active"]


class RiskObservationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskObservation
        fields = ["id", "hazard", "observer", "observation", "latitude", "longitude", "observed_at"]


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "name", "slug", "description", "cuisine_type", "price_range", "city", "country", "address", "phone", "latitude", "longitude", "is_active"]


class DestinationTransitRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationTransitRoute
        fields = ["id", "destination", "route_name", "transport_type", "departure_point", "arrival_point", "schedule", "fare"]


class TravelPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = ["id", "user", "title", "description", "start_date", "end_date", "is_public", "created_at", "updated_at"]


class TravelPlanStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlanStop
        fields = ["id", "plan", "destination", "order_index", "arrival_date", "departure_date", "notes"]


class TravelerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelerDocument
        fields = ["id", "user", "document_type", "document_number", "file", "expiry_date", "is_verified", "created_at"]


# ---------------------------------------------------------------------------
# Auth Serializers
# ---------------------------------------------------------------------------
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


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
    class Meta:
        model = InfrastructureSubmission
        fields = ["id", "user", "name", "category", "description", "latitude", "longitude", "status", "created_at"]


def is_generated_postcard_url(url):
    """Check if a URL is a generated postcard URL."""
    if not url:
        return False
    return "/postcards/" in url or url.startswith("/media/postcards/")


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
    user_id = serializers.IntegerField(required=False)
    destination_id = serializers.IntegerField(required=False)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)


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
    destination_id = serializers.IntegerField()
    date = serializers.DateField(required=False)


class SafetyPredictionResponseSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    risk_level = serializers.CharField()
    score = serializers.FloatField()
    factors = serializers.DictField(required=False)


class BudgetPredictionRequestSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    num_people = serializers.IntegerField(default=1)
    num_days = serializers.IntegerField(default=1)
    travel_mode = serializers.CharField(required=False, allow_blank=True)


class BudgetPredictionResponseSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    estimated_budget = serializers.FloatField()
    currency = serializers.CharField()
    breakdown = serializers.DictField(required=False)


class BestRouteRequestSerializer(serializers.Serializer):
    origin_id = serializers.IntegerField()
    destination_id = serializers.IntegerField()
    mode = serializers.CharField(required=False, allow_blank=True)


class BestRouteResponseSerializer(serializers.Serializer):
    origin_id = serializers.IntegerField()
    destination_id = serializers.IntegerField()
    distance_km = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    mode = serializers.CharField()
    steps = serializers.ListField(required=False)


class ItineraryRequestSerializer(serializers.Serializer):
    destination_ids = serializers.ListField(child=serializers.IntegerField())
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    num_people = serializers.IntegerField(default=1)


class ItineraryResponseSerializer(serializers.Serializer):
    days = serializers.ListField()
    total_distance_km = serializers.FloatField(required=False)
    estimated_budget = serializers.FloatField(required=False)


# ---------------------------------------------------------------------------
# Navigation Serializers
# ---------------------------------------------------------------------------
class RouteSegmentSerializer(serializers.Serializer):
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
    segments = serializers.ListField(child=RouteSegmentSerializer())
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
