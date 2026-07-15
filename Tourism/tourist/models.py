
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Languages & Users
# ---------------------------------------------------------------------------
class Language(models.Model):
    """Supported languages for translation & user preference."""

    code = models.CharField(max_length=10, unique=True, help_text="ISO 639-1 code, e.g. 'en', 'fr', 'ne'")
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        TOURIST = "tourist", "Tourist"
        GUIDE = "guide", "Local Guide"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TOURIST)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    bio = models.TextField(blank=True)

    preferred_language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )

    # Location - set from browser GPS first, GeoIP as fallback (see middleware.py)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    location_source = models.CharField(
        max_length=10,
        choices=[("gps", "Browser GPS"), ("geoip", "GeoIP"), ("manual", "Manual")],
        blank=True,
    )

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class PasswordResetToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


# ---------------------------------------------------------------------------
# Tourism module
# ---------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name / css class for frontend")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Destination(TimeStampedModel):
    class SubmissionStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="destinations")
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)

    # Cover photo supplied directly by whoever submits the place (in addition
    # to the richer multi-image DestinationImage gallery below).
    cover_image = models.ImageField(upload_to="destinations/cover/", blank=True, null=True)

    # GPS coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    opening_hours = models.CharField(max_length=255, blank=True)
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    contact_phone = PhoneNumberField(blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    ratings_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="destinations_created"
    )

    # Any logged-in tourist can submit a place. Staff-created places are
    # auto-approved; tourist-submitted places start as "pending" and only
    # become publicly visible once an admin approves them.
    is_user_submitted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.APPROVED)
    review_note = models.CharField(max_length=255, blank=True, help_text="Admin note, e.g. reason for rejection")

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["city", "country"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Destination.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def recalculate_rating(self):
        agg = self.ratings.aggregate(avg=models.Avg("value"), count=models.Count("id"))
        self.average_rating = round(agg["avg"] or 0, 2)
        self.ratings_count = agg["count"] or 0
        self.save(update_fields=["average_rating", "ratings_count"])


class DestinationTranslation(models.Model):
    """Stores machine-translated copies of a destination's text fields."""

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="translations")
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    is_auto_generated = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("destination", "language")

    def __str__(self):
        return f"{self.destination.name} [{self.language.code}]"


class DestinationImage(TimeStampedModel):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="destinations/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    is_cover = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_cover", "-created_at"]


class DestinationVideo(TimeStampedModel):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="videos")
    video_url = models.URLField(help_text="YouTube/Vimeo link or hosted video URL")
    title = models.CharField(max_length=200, blank=True)
    thumbnail = models.ImageField(upload_to="destinations/video_thumbnails/", blank=True, null=True)


class Review(TimeStampedModel):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    comment = models.TextField()
    is_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("destination", "user")


class Rating(TimeStampedModel):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = ("destination", "user")

    def __str__(self):
        return f"{self.destination.name} - {self.value}*"


class Favorite(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("user", "destination")
        ordering = ["-created_at"]


class VisitHistory(models.Model):
    """Tracks destinations a user has viewed/visited."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="history")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="visit_history")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        verbose_name_plural = "Visit history"


class Budget(TimeStampedModel):
    class ExpenseCategory(models.TextChoices):
        ACCOMMODATION = "accommodation", "Accommodation"
        FOOD = "food", "Food"
        TRANSPORT = "transport", "Transport"
        ACTIVITIES = "activities", "Activities"
        OTHER = "other", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="budget_entries"
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, default=ExpenseCategory.OTHER)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="NPR")
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]


# ---------------------------------------------------------------------------
# Alerts & Emergency Information
# ---------------------------------------------------------------------------
class Alert(TimeStampedModel):
    class AlertType(models.TextChoices):
        WEATHER = "weather", "Weather"
        FLOOD = "flood", "Flood"
        EARTHQUAKE = "earthquake", "Earthquake"
        LANDSLIDE = "landslide", "Landslide"
        HEALTH = "health", "Health"
        CRIME = "crime", "Crime"
        TRANSPORT = "transport", "Transport"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MODERATE)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    source = models.CharField(max_length=100, blank=True, help_text="e.g. OpenWeatherMap, Govt. Authority")
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["latitude", "longitude"])]


class EmergencyContact(TimeStampedModel):
    class ContactType(models.TextChoices):
        POLICE = "police", "Police"
        HOSPITAL = "hospital", "Hospital"
        TOURISM_OFFICE = "tourism_office", "Tourism Office"
        FIRE_STATION = "fire_station", "Fire Station"
        AMBULANCE = "ambulance", "Ambulance"
        EMBASSY = "embassy", "Embassy"

    contact_type = models.CharField(max_length=20, choices=ContactType.choices)
    name = models.CharField(max_length=200)
    phone_number = PhoneNumberField()
    alternate_phone = PhoneNumberField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_24_hours = models.BooleanField(default=True)

    class Meta:
        ordering = ["contact_type", "name"]
        indexes = [models.Index(fields=["latitude", "longitude"])]

    def __str__(self):
        return f"{self.get_contact_type_display()} - {self.name}"


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class Notification(TimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"
        IN_APP = "in_app", "In-App"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    related_alert = models.ForeignKey(Alert, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class DeviceToken(models.Model):
    """Push notification device tokens (FCM)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(
        max_length=10, choices=[("ios", "iOS"), ("android", "Android"), ("web", "Web")], default="web"
    )
    created_at = models.DateTimeField(auto_now_add=True)


# ---------------------------------------------------------------------------
# ML integration
# ---------------------------------------------------------------------------
class MLInsight(TimeStampedModel):
    """
    Stores results produced by the teammate's ML microservice — e.g. an
    image-authenticity/category check run on a newly submitted cover photo,
    or a personalized recommendation score. The ML service pushes these via
    the `/api/v1/ml/results/` webhook (see tourist/views_ml.py).
    """

    class InsightType(models.TextChoices):
        IMAGE_CLASSIFICATION = "image_classification", "Image Classification"
        RECOMMENDATION_SCORE = "recommendation_score", "Recommendation Score"
        CROWD_PREDICTION = "crowd_prediction", "Crowd Level Prediction"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="ml_insights")
    insight_type = models.CharField(max_length=30, choices=InsightType.choices)
    label = models.CharField(max_length=100, blank=True, help_text="e.g. predicted category, crowd level")
    score = models.FloatField(null=True, blank=True, help_text="Confidence / relevance score, 0-1")
    raw_result = models.JSONField(default=dict, blank=True, help_text="Full payload returned by the ML service")

    class Meta:
        ordering = ["-created_at"]
