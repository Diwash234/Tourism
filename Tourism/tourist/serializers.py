from django.contrib.auth import password_validation
from django.utils import timezone
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
    DeviceToken,
    MLInsight,
)
from .utils import haversine_distance


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

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone_number", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name", "phone_number",
            "role", "profile_picture", "bio", "preferred_language",
            "latitude", "longitude", "country", "city", "location_source",
            "is_verified", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "date_joined", "location_source"]


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

    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)


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
    class Meta:
        model = DestinationImage
        fields = ["id", "destination", "image", "caption", "is_cover", "created_at"]
        read_only_fields = ["created_at"]


class DestinationVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationVideo
        fields = ["id", "destination", "video_url", "title", "thumbnail", "created_at"]
        read_only_fields = ["created_at"]


class DestinationTranslationSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source="language.code", read_only=True)

    class Meta:
        model = DestinationTranslation
        fields = ["id", "language", "language_code", "name", "description", "short_description", "is_auto_generated"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "destination", "user", "user_name", "comment", "is_flagged", "created_at", "updated_at"]
        read_only_fields = ["user", "is_flagged", "created_at", "updated_at"]

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


class DestinationListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "category", "category_name", "short_description",
            "latitude", "longitude", "city", "country", "average_rating", "ratings_count",
            "views_count", "entry_fee", "cover_image_url", "distance_km",
            "status", "is_user_submitted", "is_active",
        ]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        cover = obj.gallery.filter(is_cover=True).first() or obj.gallery.first()
        if cover:
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj):
        """Straight-line distance FROM the requesting user's location TO this place."""
        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")
        if user_lat is not None and user_lon is not None:
            return round(haversine_distance(user_lat, user_lon, obj.latitude, obj.longitude), 2)
        return None


class DestinationDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    gallery = DestinationImageSerializer(many=True, read_only=True)
    videos = DestinationVideoSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    translations = DestinationTranslationSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "name", "slug", "category", "category_name", "description", "short_description",
            "cover_image_url", "latitude", "longitude", "address", "city", "country", "opening_hours",
            "entry_fee", "contact_phone", "contact_email", "website", "average_rating", "ratings_count",
            "views_count", "created_by", "created_by_name", "is_user_submitted", "status", "review_note",
            "is_active", "created_at", "updated_at", "gallery", "videos", "reviews", "translations", "distance_km",
        ]
        read_only_fields = [
            "slug", "average_rating", "ratings_count", "views_count", "created_by",
            "is_user_submitted", "status", "review_note", "created_at", "updated_at",
        ]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        return None

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj):
        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")
        if user_lat is not None and user_lon is not None:
            return round(haversine_distance(user_lat, user_lon, obj.latitude, obj.longitude), 2)
        return None


class DestinationWriteSerializer(serializers.ModelSerializer):
    """
    Used for both admin-created and tourist-submitted places. `cover_image`
    is accepted directly in the same multipart request (no separate gallery
    upload call needed for the main photo).
    """

    class Meta:
        model = Destination
        fields = [
            "id", "name", "category", "description", "short_description", "cover_image",
            "latitude", "longitude", "address", "city", "country", "opening_hours",
            "entry_fee", "contact_phone", "contact_email", "website", "is_active",
        ]

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
        return super().create(validated_data)


class DestinationApprovalSerializer(serializers.Serializer):
    """Used by admins to approve or reject a pending, tourist-submitted place."""

    status = serializers.ChoiceField(choices=[Destination.SubmissionStatus.APPROVED, Destination.SubmissionStatus.REJECTED])
    review_note = serializers.CharField(required=False, allow_blank=True)


class NearbyDestinationQuerySerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
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
            "latitude", "longitude", "city", "country", "source",
            "is_active", "starts_at", "ends_at", "created_at", "distance_km",
        ]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj):
        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")
        if user_lat is not None and user_lon is not None and obj.latitude is not None:
            return round(haversine_distance(user_lat, user_lon, obj.latitude, obj.longitude), 2)
        return None


class EmergencyContactSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyContact
        fields = [
            "id", "contact_type", "name", "phone_number", "alternate_phone",
            "address", "city", "country", "latitude", "longitude",
            "is_24_hours", "distance_km",
        ]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj):
        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")
        if user_lat is not None and user_lon is not None:
            return round(haversine_distance(user_lat, user_lon, obj.latitude, obj.longitude), 2)
        return None


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "channel", "title", "message", "is_read", "is_sent", "related_alert", "created_at"]
        read_only_fields = ["channel", "title", "message", "is_sent", "related_alert", "created_at"]


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
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
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
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)

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