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
        # Original 3 kept as-is (existing users/checks referencing these
        # values keep working unchanged) -- 10 more added per the RBAC spec.
        TOURIST = "tourist", "Tourist"
        GUIDE = "guide", "Local Guide"
        ADMIN = "admin", "Admin"
        SUPER_ADMIN = "super_admin", "Super Admin"
        TOURISM_ADMIN = "tourism_admin", "Tourism Admin"
        CONTENT_MODERATOR = "content_moderator", "Content Moderator"
        DISTRICT_MANAGER = "district_manager", "District Manager"
        HOTEL_MANAGER = "hotel_manager", "Hotel Manager"
        STAFF = "staff", "Staff"
        TOURIST_POLICE = "tourist_police", "Tourist Police"
        POLICE = "police", "Police"
        HOSPITAL_STAFF = "hospital_staff", "Hospital Staff"
        RESCUE_TEAM = "rescue_team", "Rescue Team"
        EMERGENCY_OPERATOR = "emergency_operator", "Emergency Operator"
        QA_TESTER = "qa_tester", "QA Tester"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    phone_verified = models.BooleanField(default=False)

    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email/Password"
        GOOGLE = "google", "Google"
        GITHUB = "github", "GitHub"

    auth_provider = models.CharField(max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL)
    provider_uid = models.CharField(
        max_length=255, blank=True,
        help_text="The account ID from Google/GitHub, used to re-link on subsequent OAuth logins."
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TOURIST)
    managed_district = models.CharField(
        max_length=100, blank=True,
        help_text="For District Manager role: which district this user can manage. Blank = no district restriction."
    )
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


class StaffCapabilityProfile(TimeStampedModel):
    """Granular module/action permissions layered on the existing User role."""
    MODULES = ["dashboard", "destinations", "images", "content", "budget", "datasets", "hotels", "reviews", "safety", "feedback", "audit", "users", "settings"]
    ACTIONS = ["view", "add", "change", "delete", "approve", "export", "train", "assign"]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="capability_profile")
    capabilities = models.JSONField(default=dict, blank=True, help_text='{"destinations":["view","change"],"images":["view","approve"]}')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="capability_profiles_assigned")
    managed_districts = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        invalid_modules = set(self.capabilities) - set(self.MODULES)
        invalid_actions = {action for actions in self.capabilities.values() for action in actions if action not in self.ACTIONS}
        if invalid_modules or invalid_actions:
            raise ValidationError(f"Invalid modules/actions: {invalid_modules or invalid_actions}")

    def allows(self, module, action="view"):
        if not self.is_active:
            return False
        return action in self.capabilities.get(module, []) or "*" in self.capabilities.get(module, [])


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class SMSVerificationToken(models.Model):
    """
    6-digit OTP sent via Twilio to verify a phone number. Mirrors
    EmailVerificationToken's shape/pattern but uses a short numeric code
    (not a UUID) since it has to be readable and typeable from an SMS.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sms_tokens")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.PositiveSmallIntegerField(default=0)  # brute-force guard

    def is_valid(self):
        return not self.is_used and self.attempt_count < 5 and timezone.now() < self.expires_at


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
        ARCHIVED = "archived", "Archived"


    external_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True
    )

    city_nepali = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    city_english = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="destinations",
        null=True,
        blank=True
    )


    type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    description = models.TextField(
        blank=True,
        null=True
    )


    short_description = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )


    district = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    municipality = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Metropolitan, Sub-Metropolitan, Municipality, or Rural Municipality (Gaunpalika)"
    )

    ward_number = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Local Ward Number (e.g. 1 to 35)"
    )

    province = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    source = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    cover_image = models.ImageField(
        upload_to="destinations/cover/",
        blank=True,
        null=True
    )


    # GPS coordinates
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )


    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    country = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    opening_hours = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    aliases = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Alternative names, local spellings, e.g. Waling / Walling / Waling Bazaar"
    )

    cultural_significance = models.TextField(
        blank=True,
        null=True,
        help_text="Cultural importance and local traditions"
    )

    religious_significance = models.TextField(
        blank=True,
        null=True,
        help_text="Religious history, temples, and sacred lore"
    )

    tourism_importance = models.TextField(
        blank=True,
        null=True,
        help_text="Why tourists visit this destination"
    )

    food_cuisine_info = models.TextField(
        blank=True,
        null=True,
        help_text="Local cuisine, delicacies, and food experiences"
    )

    travel_safety_tips = models.TextField(
        blank=True,
        null=True,
        help_text="Practical safety tips and local advice"
    )

    distance_from_kathmandu_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    distance_from_nearest_city_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    nearest_major_city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    distance_from_nearest_airport_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    nearest_airport_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    approx_travel_time = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g. 5h 30m by bus / 25m by flight"
    )

    recommended_days = models.PositiveSmallIntegerField(
        default=2,
        null=True,
        blank=True
    )

    research_status = models.CharField(
        max_length=30,
        choices=[
            ("draft", "Draft"),
            ("researching", "Researching"),
            ("review_required", "Review Required"),
            ("approved", "Approved"),
            ("published", "Published"),
            ("rejected", "Rejected")
        ],
        default="published"
    )

    history = models.TextField(
        blank=True,
        null=True,
        help_text="Historical, religious, or cultural background"
    )

    best_time_to_visit = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="e.g. Sep-Nov (Autumn) & Mar-May (Spring)"
    )

    altitude = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Altitude in meters (e.g. 1,400m / 5,364m)"
    )

    nearest_hospital_info = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    nearest_hotel_info = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    nearest_police_info = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    entry_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )


    contact_phone = PhoneNumberField(
        blank=True,
        null=True
    )


    contact_email = models.EmailField(
        blank=True,
        null=True
    )


    website = models.URLField(
        blank=True,
        null=True
    )


    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )


    ratings_count = models.PositiveIntegerField(
        default=0
    )


    views_count = models.PositiveIntegerField(
        default=0
    )


    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="destinations_created"
    )


    is_user_submitted = models.BooleanField(
        default=False
    )


    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.APPROVED
    )


    review_note = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Admin note, e.g. reason for rejection"
    )


    is_active = models.BooleanField(
        default=True
    )


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

        agg = self.ratings.aggregate(
            avg=models.Avg("value"),
            count=models.Count("id")
        )

        self.average_rating = round(agg["avg"] or 0, 2)
        self.ratings_count = agg["count"] or 0

        self.save(
            update_fields=[
                "average_rating",
                "ratings_count"
            ]
        )


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
    class Source(models.TextChoices):
        ADMIN = "admin", "Admin Upload"
        USER_UPLOAD = "user_upload", "Community Upload"
        UNSPLASH = "unsplash", "Unsplash"
        WIKIMEDIA = "wikimedia", "Wikimedia Commons"
        GOOGLE_PLACES = "google_places", "Google Places"
        FOURSQUARE = "foursquare", "Foursquare"
        AI_GENERATED = "ai_generated", "AI Generated"
        REFERENCE = "reference", "Reference Image"
        IMAGE_SERVER = "image_server", "Standalone Image Server"

    class ImageStatus(models.TextChoices):
        PENDING = "pending", "Needs Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="destinations/gallery/", blank=True, null=True)
    external_url = models.URLField(
        blank=True, help_text="Used instead of `image` for externally-hosted photos (Unsplash/Wikimedia/etc.)"
    )
    thumbnail_url = models.URLField(blank=True, help_text="Optimized thumbnail for fast web delivery")
    image_path = models.CharField(
        max_length=500, blank=True,
        help_text="Relative path on the standalone image server, e.g. nepal/kathmandu/001.webp. "
                  "When set, the full URL is IMAGE_BASE_URL + /images/ + image_path and the "
                  "binary is served by the image server, never by Django.",
    )
    alt_text = models.CharField(max_length=255, blank=True, help_text="Accessible alt text for the image")
    ordering = models.PositiveIntegerField(default=0, help_text="Display order within the destination gallery")
    caption = models.CharField(max_length=200, blank=True)
    is_cover = models.BooleanField(default=False)

    source = models.CharField(max_length=20, choices=Source.choices, default=Source.ADMIN)
    source_url = models.URLField(max_length=500, blank=True, null=True, help_text="Original source page URL")
    source_platform = models.CharField(max_length=100, blank=True, default="Wikimedia Commons")
    photographer = models.CharField(max_length=150, blank=True, null=True)
    license_type = models.CharField(max_length=100, blank=True, default="Creative Commons CC BY-SA / Unsplash")
    copyright_status = models.CharField(max_length=50, default="verified_reusable")
    image_category = models.CharField(max_length=50, default="attraction")

    # --- AI generation provenance ---
    generation_provider = models.CharField(max_length=50, blank=True, help_text="openai / stability / google / flux")
    generation_model = models.CharField(max_length=100, blank=True)
    generation_prompt = models.TextField(blank=True)
    negative_prompt = models.TextField(blank=True)
    generation_seed = models.BigIntegerField(null=True, blank=True)
    generation_job = models.ForeignKey(
        "ImageGenerationJob", on_delete=models.SET_NULL, null=True, blank=True, related_name="outputs"
    )

    # --- Automated quality / authenticity scores (0..1) ---
    quality_score = models.FloatField(null=True, blank=True)
    realism_score = models.FloatField(null=True, blank=True)
    authenticity_score = models.FloatField(null=True, blank=True, help_text="Nepal authenticity")
    destination_match_score = models.FloatField(null=True, blank=True)
    duplicate_score = models.FloatField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)

    # pHash / dHash for duplicate detection
    phash = models.CharField(max_length=32, blank=True, db_index=True)

    verification_status = models.CharField(
        max_length=20, choices=ImageStatus.choices, default=ImageStatus.APPROVED
    )
    is_verified = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_photos"
    )
    attribution = models.CharField(
        max_length=255, blank=True, help_text="Required for Unsplash/Wikimedia per their license terms"
    )
    is_promoted = models.BooleanField(
        default=False, help_text="Auto-set true once a community upload crosses the popularity threshold"
    )
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_cover", "ordering", "-is_promoted", "-view_count", "-created_at"]
        indexes = [
            models.Index(fields=["destination", "ordering"], name="destimg_dest_order_idx"),
            models.Index(fields=["image_path"], name="destimg_path_idx"),
        ]

    def __str__(self):
        return f"{self.destination.name} photo ({self.get_source_display()})"


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
    moderation_status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("approved", "Approved"), ("flagged", "Flagged"), ("archived", "Archived")], default="approved", db_index=True)
    moderation_note = models.TextField(blank=True)
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="destination_reviews_moderated")
    moderated_at = models.DateTimeField(null=True, blank=True)

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


class Hotel(TimeStampedModel):
    """
    Accommodation options near a destination. Populated either from your
    dataset (see `import_hotels` management command) or from external APIs
    (Google Places / Foursquare) via `tourist/utils.py`.
    """
    phone = models.CharField(max_length=30, blank=True)

    class BookingStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        UNAVAILABLE = "unavailable", "Unavailable"
        UNKNOWN = "unknown", "Unknown"
    

    class Source(models.TextChoices):
        DATASET = "dataset", "Imported Dataset"
        GOOGLE_PLACES = "google_places", "Google Places"
        FOURSQUARE = "foursquare", "Foursquare"
        MANUAL = "manual", "Manually Added"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="hotels")
    name = models.CharField(max_length=200)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    booking_status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.UNKNOWN)
    booking_url = models.URLField(blank=True, help_text="Link to book externally (e.g. Booking.com, Google)")
    cover_image = models.ImageField(upload_to="hotels/covers/", blank=True, null=True)
    external_image_url = models.URLField(
        blank=True,
        help_text="Used instead of cover_image for externally-hosted photos (Unsplash/Wikimedia/etc.)."
    )
    facilities = models.JSONField(
        default=list, blank=True,
        help_text='e.g. ["wifi", "breakfast", "parking", "pool", "ac"]'
    )
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.DATASET)
    source_url = models.URLField(max_length=600, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-rating", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_booking_status_display()})";

class Hospital(models.Model):

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="hospitals"
    )

    name = models.CharField(max_length=200)

    address = models.CharField(max_length=300)

    phone = models.CharField(max_length=50)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)

    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    district = models.CharField(max_length=100)
    image = models.ImageField(upload_to="services/hospitals/", blank=True, null=True)
    opening_hours = models.CharField(max_length=160, blank=True)
    emergency_available = models.BooleanField(default=True)
    source_name = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(max_length=600, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class PoliceStation(models.Model):

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="police_stations"
    )

    name = models.CharField(max_length=200)

    address = models.CharField(max_length=300)

    phone = models.CharField(max_length=50)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)

    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    image = models.ImageField(upload_to="services/police/", blank=True, null=True)
    opening_hours = models.CharField(max_length=160, blank=True)
    emergency_available = models.BooleanField(default=True)
    source_name = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(max_length=600, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class BudgetEstimation(models.Model):
    destination = models.OneToOneField(
        Destination,
        on_delete=models.CASCADE,
        related_name="budget_estimation"
    )

    district = models.CharField(max_length=100)

    province = models.CharField(max_length=100)

    transport_cost = models.DecimalField(max_digits=8, decimal_places=2)

    food_cost_per_day = models.DecimalField(max_digits=8, decimal_places=2)

    accommodation_per_night = models.DecimalField(max_digits=8, decimal_places=2)

    local_transport = models.DecimalField(max_digits=8, decimal_places=2)

    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    estimated_daily_budget = models.DecimalField(max_digits=8, decimal_places=2)

    estimated_trip_budget = models.DecimalField(max_digits=8, decimal_places=2)


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

    source = models.CharField(max_length=100, blank=True, help_text="e.g. DHM, BIPAD, Nepal Police, verified news desk")
    source_url = models.URLField(max_length=600, blank=True)
    is_verified = models.BooleanField(default=False)
    radius_km = models.FloatField(default=4.0, validators=[MinValueValidator(0.5), MaxValueValidator(100)])
    municipality = models.CharField(max_length=160, blank=True)
    district = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=120, blank=True)
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
        WARD_OFFICE = "ward_office", "Ward Office"
        WARD_MEMBER = "ward_member", "Local Ward Member"

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

    # Only meaningful for WARD_OFFICE / WARD_MEMBER rows — local governance
    # contacts tied to a specific municipal ward.
    ward_number = models.PositiveIntegerField(null=True, blank=True, help_text="Local ward number (ward contacts only)")
    designation = models.CharField(
        max_length=100, blank=True,
        help_text="Role, e.g. 'Ward Chairperson', 'Ward Member - Female', 'Ward Secretary' (ward contacts only)",
    )

    class Meta:
        ordering = ["contact_type", "ward_number", "name"]
        indexes = [models.Index(fields=["latitude", "longitude"]), models.Index(fields=["ward_number"])]

    def __str__(self):
        if self.ward_number:
            return f"{self.get_contact_type_display()} (Ward {self.ward_number}) - {self.name}"
        return f"{self.get_contact_type_display()} - {self.name}"
class RiskAnalysis(models.Model):
    """Imported/modelled baseline risk features for a destination."""

    destination = models.OneToOneField(
        Destination,
        on_delete=models.CASCADE,
        related_name="risk_analysis"
    )
    accidents = models.IntegerField(default=0)
    landslide = models.IntegerField(default=0)
    avalanche = models.IntegerField(default=0)
    flood = models.IntegerField(default=0)
    earthquake_damage = models.IntegerField(default=0)
    hospital_count = models.IntegerField(default=0)
    police_count = models.IntegerField(default=0)
    fire_station_count = models.IntegerField(default=0)
    emergency_risk = models.FloatField()
    natural_disaster_risk = models.FloatField()
    tourism_risk_index = models.FloatField()
    risk_category = models.CharField(max_length=50)


class RiskIncident(TimeStampedModel):
    """A dated, source-attributed historical incident (not a live warning)."""

    class HazardType(models.TextChoices):
        FLOOD = "flood", "Flood"
        LANDSLIDE = "landslide", "Landslide"
        AVALANCHE = "avalanche", "Avalanche"
        EARTHQUAKE = "earthquake", "Earthquake"
        GLOF = "glof", "Glacial lake outburst flood"
        HEAVY_RAIN = "heavy_rain", "Heavy rain"
        SNOWSTORM = "snowstorm", "Snowstorm"
        FOREST_FIRE = "forest_fire", "Forest fire"
        LIGHTNING = "lightning", "Lightning"
        ROAD_ACCIDENT = "road_accident", "Road accident"
        HEALTH = "health", "Health / altitude"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class SourceType(models.TextChoices):
        CSV_IMPORT = "csv_import", "CSV import"
        ADMIN = "admin", "Admin verified"
        OFFICIAL = "official", "Official authority"
        NEWS = "news", "News report"
        API = "api", "External API"
        USER = "user", "Traveler report"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="risk_incidents")
    hazard_type = models.CharField(max_length=30, choices=HazardType.choices)
    event_date = models.DateField()
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=12, choices=Severity.choices, default=Severity.MODERATE)
    fatalities = models.PositiveIntegerField(default=0)
    injuries = models.PositiveIntegerField(default=0)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.ADMIN)
    source_name = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(max_length=600, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    municipality = models.CharField(max_length=160, blank=True)
    affected_area = models.CharField(max_length=240, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-event_date", "-created_at"]
        indexes = [models.Index(fields=["destination", "event_date"]), models.Index(fields=["hazard_type"])]


class CurrentHazard(TimeStampedModel):
    """Time-bounded observation/warning kept separate from model predictions."""

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="current_hazards")
    hazard_type = models.CharField(max_length=30, choices=RiskIncident.HazardType.choices)
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=12, choices=RiskIncident.Severity.choices, default=RiskIncident.Severity.MODERATE)
    source_type = models.CharField(max_length=20, choices=RiskIncident.SourceType.choices, default=RiskIncident.SourceType.OFFICIAL)
    source_name = models.CharField(max_length=160)
    source_url = models.URLField(max_length=600, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    observed_at = models.DateTimeField()
    affected_area = models.CharField(max_length=240, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    station_name = models.CharField(max_length=160, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-observed_at"]
        indexes = [models.Index(fields=["destination", "is_active", "observed_at"])]

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    safety_alerts = models.BooleanField(default=True)
    booking_updates = models.BooleanField(default=True)
    recommendations = models.BooleanField(default=True)
    marketing = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    def __str__(self): return f"Notification preferences for {self.user.email}"


class Notification(TimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"
        IN_APP = "in_app", "In-App"

    class DeliveryStatus(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    class Category(models.TextChoices):
        GENERAL = "general", "General"
        SAFETY = "safety", "Safety"
        BOOKING = "booking", "Booking"
        RECOMMENDATION = "recommendation", "Recommendation"
        MARKETING = "marketing", "Marketing"
        FEEDBACK = "feedback", "Feedback"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    batch_id = models.UUIDField(null=True, blank=True, db_index=True)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL, db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    delivery_status = models.CharField(max_length=12, choices=DeliveryStatus.choices, default=DeliveryStatus.QUEUED, db_index=True)
    delivery_attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    related_alert = models.ForeignKey(Alert, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["delivery_status", "next_retry_at"]), models.Index(fields=["user", "is_read"])]

    def save(self, *args, **kwargs):
        if self._state.adding and self.channel == self.Channel.IN_APP and self.delivery_status == self.DeliveryStatus.QUEUED:
            self.delivery_status = self.DeliveryStatus.SENT
            self.is_sent = True
            self.sent_at = timezone.now()
        super().save(*args, **kwargs)


class TrustedContact(models.Model):
    """
    A person a user has designated to receive safety alerts / shared trip
    access. Doesn't need their own account -- identified by email or
    phone, contacted directly when needed (SOS, trip share links).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trusted_contacts")
    name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=100, blank=True, help_text="e.g. 'Parent', 'Spouse', 'Friend'")
    email = models.EmailField(blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.relationship or 'contact'}) for {self.user}"


class SharedTrip(models.Model):
    """
    A live location share the user has explicitly turned on. The
    `share_token` is what a TrustedContact uses to view it -- no account
    needed on their end, just the (unguessable, revocable) link.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shared_trips")
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    label = models.CharField(max_length=150, blank=True, help_text="e.g. 'Annapurna trek, Day 3'")
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Auto-expires -- a share link should never stay valid forever.")
    trusted_contacts = models.ManyToManyField(TrustedContact, related_name="shared_trips", blank=True)

    class Meta:
        ordering = ["-started_at"]

    def is_valid(self):
        return self.is_active and timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.label or 'Trip'} ({self.user}) -- {'active' if self.is_valid() else 'expired/ended'}"


class LocationPing(models.Model):
    """
    One GPS position update during an active SharedTrip. Polling-based
    (the trusted contact's view re-fetches the latest ping every N
    seconds) rather than WebSocket push -- simpler to build correctly
    first; true real-time (Django Channels) is a bigger, separate
    addition if genuinely needed later.
    """
    trip = models.ForeignKey(SharedTrip, on_delete=models.CASCADE, related_name="pings")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]


class SOSAlert(models.Model):
    """
    An emergency trigger during a trip (shared or not). Kept separate
    from SharedTrip so an SOS can be raised even with no active share
    (e.g. share it retroactively / the app auto-starts one) -- the trip
    FK is optional for that reason.
    """
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"
        FALSE_ALARM = "false_alarm", "False Alarm"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sos_alerts")
    trip = models.ForeignKey(SharedTrip, on_delete=models.SET_NULL, null=True, blank=True, related_name="sos_alerts")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notified_contacts = models.ManyToManyField(TrustedContact, related_name="sos_alerts", blank=True)

    class Meta:
        ordering = ["-triggered_at"]

    def __str__(self):
        return f"SOS from {self.user} ({self.status})"


class FamilyLink(models.Model):
    """
    Account-to-account family linking (unlike TrustedContact, both sides
    have accounts here). A link is requested by `requester`, accepted by
    `member`. Once accepted, either side can:
      * see the other's live location while a SharedTrip is active,
      * see the other's recent trip history + SOS history,
      * get an in-app Notification when the other starts a trip or
        triggers an SOS.
    """
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_links_sent")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_links_received")
    relationship = models.CharField(max_length=100, blank=True, help_text="e.g. 'Parent', 'Spouse', 'Sibling'")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["requester", "member"], name="unique_family_link_pair"),
        ]

    def __str__(self):
        return f"FamilyLink {self.requester_id} -> {self.member_id} ({self.status})"


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


# ---------------------------------------------------------------------------
# OpenStreetMap (Overpass API) data — persisted, not just live pass-through.
# See tourist/services/overpass.py for the sync functions that populate these.
# ---------------------------------------------------------------------------
class OSMEssentialService(TimeStampedModel):
    class Category(models.TextChoices):
        HOSPITAL = "hospital", "Hospital"
        CLINIC = "clinic", "Clinic"
        PHARMACY = "pharmacy", "Pharmacy"
        POLICE = "police", "Police"
        ARMED_FORCE = "armed_force", "Armed Force"
        FIRE_STATION = "fire_station", "Fire Station"
        BANK = "bank", "Bank"
        BLOOD_BANK = "blood_bank", "Blood Bank"
        ATM = "atm", "ATM"
        AMBULANCE = "ambulance", "Ambulance"
        MUNICIPALITY_OFFICE = "municipality_office", "Municipality Office"
        TOURISM_OFFICE = "tourism_office", "Tourism Information Office"

    osm_id = models.CharField(max_length=50, unique=True, help_text="OSM type/id, e.g. 'node/123456'")
    category = models.CharField(max_length=30, choices=Category.choices)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="services/essential/", blank=True, null=True)
    source_name = models.CharField(max_length=160, blank=True, default="OpenStreetMap")
    source_url = models.URLField(max_length=600, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    opening_hours = models.CharField(max_length=160, blank=True)
    emergency_available = models.BooleanField(default=False)
    raw_tags = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["category", "name"]
        indexes = [models.Index(fields=["latitude", "longitude"]), models.Index(fields=["category"])]

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class OSMTourismPlace(TimeStampedModel):
    class Category(models.TextChoices):
        ATTRACTION = "attraction", "Attraction"
        VIEWPOINT = "viewpoint", "Viewpoint"
        MUSEUM = "museum", "Museum"
        HOTEL = "hotel", "Hotel"
        INFORMATION = "information", "Information"
        RESTAURANT = "restaurant", "Restaurant"
        CAFE = "cafe", "Cafe"
        MONUMENT = "monument", "Monument"
        PEAK = "peak", "Natural Peak"
        WATERFALL = "waterfall", "Waterfall"
        HIKING_PATH = "hiking_path", "Hiking Path"
        HIKING_ROUTE = "hiking_route", "Hiking Route"

    osm_id = models.CharField(max_length=50, unique=True, help_text="OSM type/id, e.g. 'way/123456'")
    category = models.CharField(max_length=30, choices=Category.choices)
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255, blank=True)
    raw_tags = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["category", "name"]
        indexes = [models.Index(fields=["latitude", "longitude"]), models.Index(fields=["category"])]

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class DestinationAuditLog(TimeStampedModel):
    """
    One row per moderation action on a Destination -- submitted, approved,
    rejected, archived, edited. Tracks who did what and when.
    """
    class Action(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"
        EDITED = "edited", "Edited"

    destination = models.ForeignKey(
        "Destination", on_delete=models.CASCADE, related_name="audit_log"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Who performed this action (null for system-generated entries)."
    )
    note = models.TextField(blank=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.destination.name}: {self.action} by {self.actor or 'system'}"


# ---------------------------------------------------------------------------
# ML-Connected Traveler & Field Staff Feedback (Expenses & Risk)
# ---------------------------------------------------------------------------
class TravelExpenseFeedback(TimeStampedModel):
    """
    Field / traveler real expenditure records. Connects directly to the
    ML budget estimation engine so subsequent calculations learn from
    actual ground spending.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expense_submissions"
    )
    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expense_feedbacks"
    )
    destination_name = models.CharField(max_length=200)
    num_people = models.PositiveIntegerField(default=1)
    num_days = models.PositiveIntegerField(default=1)
    travel_mode = models.CharField(max_length=100, default="Tourist Bus")
    accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    travel_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entry_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    food_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    route_details = models.TextField(blank=True, help_text="Practical route or transit details taken")
    is_employee_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.total_cost or self.total_cost == 0:
            self.total_cost = (
                (self.accommodation_cost or 0) +
                (self.travel_cost or 0) +
                (self.entry_cost or 0) +
                (self.food_cost or 0) +
                (self.extra_cost or 0)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.destination_name} - {self.total_cost} NPR ({self.num_days} days, {self.num_people} ppl)"


class TravelRiskFeedback(TimeStampedModel):
    """
    Detailed traveler risk & safety feedback: altitude sickness, hazards,
    transport ease, helpfulness of locals, greeting/hospitality rating.
    Connects to ML Risk scoring and real-time safety index calculations.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="risk_submissions"
    )
    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="risk_feedbacks"
    )
    destination_name = models.CharField(max_length=200)
    became_sick = models.BooleanField(default=False)
    sickness_type = models.CharField(
        max_length=100, blank=True,
        help_text="e.g. Altitude Sickness (AMS), Food Poisoning, Dehydration, Cold/Hypothermia"
    )
    misleading_activities = models.BooleanField(default=False)
    misleading_details = models.TextField(blank=True)
    accident_occurred = models.BooleanField(default=False)
    accident_details = models.TextField(blank=True)
    hazard_witnessed = models.CharField(
        max_length=100, blank=True, default="None",
        help_text="e.g. Landslide, Avalanche, Flood, Heavy Snow, Rockfall, None"
    )
    transport_accessibility_rating = models.PositiveSmallIntegerField(
        default=4, help_text="1 (Hard to reach / 4WD only) to 5 (Direct highway / flight)"
    )
    people_helpfulness_rating = models.PositiveSmallIntegerField(
        default=5, help_text="1 (Unhelpful) to 5 (Extremely friendly & helpful)"
    )
    greeting_behavior_rating = models.PositiveSmallIntegerField(
        default=5, help_text="1 (Hostile) to 5 (Very warm & respectful)"
    )
    overall_safety_rating = models.FloatField(default=9.0, help_text="Safety score from 1.0 to 10.0")
    comments = models.TextField(blank=True)
    is_admin_verified = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verified_risk_feedbacks",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.destination_name} safety report - {self.overall_safety_rating}/10"


# ---------------------------------------------------------------------------
# Destination Discovery & Research Entities (Sources, Activities, Routes)
# ---------------------------------------------------------------------------
class DestinationSource(TimeStampedModel):
    """
    Authoritative citations & references for researched destination facts.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="sources")
    title = models.CharField(max_length=200)
    source_url = models.URLField(max_length=500)
    source_type = models.CharField(
        max_length=100, default="Official Government / Tourism Portal",
        help_text="e.g. Nepal Tourism Board, Municipality Profile, Wikimedia Heritage Index, OpenStreetMap"
    )
    is_verified = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.source_type})"


class DestinationActivity(TimeStampedModel):
    """
    Activities and experiences available at the destination.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="activities")
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    difficulty_level = models.CharField(
        max_length=50, default="Easy",
        choices=[("Easy", "Easy"), ("Moderate", "Moderate"), ("Challenging", "Challenging"), ("Strenuous", "Strenuous")]
    )
    estimated_duration = models.CharField(max_length=50, blank=True, help_text="e.g. 2-3 hours / Half Day")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} at {self.destination.name}"


class DestinationAttraction(TimeStampedModel):
    """
    Specific points of interest, shrines, viewpoints, or landmarks.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="attractions")
    name = models.CharField(max_length=150)
    attraction_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    distance_from_center_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class DestinationTransitRoute(TimeStampedModel):
    """
    Available transportation options, routes, conditions, and fares.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="transit_routes")
    origin = models.CharField(max_length=150, help_text="e.g. Kathmandu (Kalanki) / Pokhara / Nearest Airport")
    transport_mode = models.CharField(max_length=100, default="Public Deluxe Bus")
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    approx_duration = models.CharField(max_length=100, help_text="e.g. 5 hours 30 mins")
    road_condition = models.CharField(max_length=150, blank=True, default="Paved Highway")
    key_stops = models.TextField(blank=True, help_text="Major transit waypoints along the route")
    estimated_fare_npr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    route_source = models.CharField(max_length=200, blank=True, default="Nepal Highway Authority & Local Transit")

    class Meta:
        ordering = ["distance_km"]

    def __str__(self):
        return f"{self.origin} ➔ {self.destination.name} via {self.transport_mode}"


class DestinationNearbyPlace(TimeStampedModel):
    """
    Nearby attractions, monasteries, waterfalls, lakes, and viewpoints.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="nearby_places")
    name = models.CharField(max_length=150)
    place_type = models.CharField(max_length=100, default="Viewpoint / Landmark")
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=5.0)
    direction = models.CharField(max_length=50, blank=True, help_text="e.g. North-West / 15 mins hike")
    short_info = models.TextField(blank=True)

    class Meta:
        ordering = ["distance_km"]

    def __str__(self):
        return f"{self.name} (~{self.distance_km} km from {self.destination.name})"


# =============================================================================
# MASS DISCOVERY & PLACE INTELLIGENCE PIPELINE MODELS
# =============================================================================

class DestinationCandidate(TimeStampedModel):
    """
    Intermediate staging repository for discovered places from multiple sources
    (OSM, Wikidata, Official Gazetteers, Topographic Surveys) before promotion
    to production Destination table.
    """
    class DiscoveryStatus(models.TextChoices):
        DISCOVERED = "discovered", "Discovered"
        CANDIDATE = "candidate", "Candidate"
        VERIFIED = "verified", "Verified"
        ENRICHED = "enriched", "Enriched"
        NEEDS_REVIEW = "needs_review", "Needs Review"
        PUBLISHED = "published", "Published to Destination"
        REJECTED = "rejected", "Rejected"
        MERGED_DUPLICATE = "merged_duplicate", "Merged Duplicate"

    class DuplicateStatus(models.TextChoices):
        NONE = "none", "No Duplicate Found"
        EXACT_MATCH = "exact_match", "Exact Name Match"
        HIGH_SIMILARITY = "high_similarity", "High Name & Location Similarity"
        PROXIMITY_OVERLAP = "proximity_overlap", "Spatial Proximity Overlap (< 500m)"
        ALIAS_OF = "alias_of", "Recognized Alias of Known Destination"

    class PlaceType(models.TextChoices):
        MOUNTAIN = "mountain", "Mountain Peak / Summit"
        HILL = "hill", "Scenic Hill / Danda"
        LAKE = "lake", "Lake / Kund / Tal"
        RIVER = "river", "River / Stream / Rafting"
        WATERFALL = "waterfall", "Waterfall / Chhango"
        TEMPLE = "temple", "Temple / Mandir"
        MONASTERY = "monastery", "Monastery / Gompa"
        STUPA = "stupa", "Stupa / Chorten"
        SHRINE = "shrine", "Sacred Shrine / Pilgrimage"
        VIEWPOINT = "viewpoint", "Panoramic Viewpoint"
        TREK_ROUTE = "trek_route", "Trek Route / Alpine Pass"
        NATIONAL_PARK = "national_park", "National Park / Reserve"
        CONSERVATION_AREA = "conservation_area", "Conservation Area"
        CAVE = "cave", "Cave / Gupha"
        PASS = "pass", "Mountain Pass / La"
        HOT_SPRING = "hot_spring", "Natural Hot Spring / Tatopani"
        HISTORIC_SITE = "historic_site", "Historic Fort / Durbar"
        VILLAGE = "village", "Traditional Settlement / Homestay"
        MUSEUM = "museum", "Museum / Cultural Centre"
        ATTRACTION = "attraction", "Tourism Attraction"
        OTHER = "other", "Other Geographic Feature"

    name = models.CharField(max_length=200)
    normalized_name = models.CharField(max_length=200, db_index=True)
    alternate_names = models.JSONField(default=list, blank=True, help_text="List of aliases (Nepali, Devanagari, romanized)")
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    altitude = models.CharField(max_length=50, blank=True, help_text="e.g. 2,175m / 7,135 ft")

    province = models.CharField(max_length=100, blank=True, db_index=True)
    district = models.CharField(max_length=100, blank=True, db_index=True)
    municipality = models.CharField(max_length=150, blank=True, db_index=True)
    ward_number = models.IntegerField(null=True, blank=True)

    place_type = models.CharField(max_length=50, choices=PlaceType.choices, default=PlaceType.ATTRACTION, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="candidate_places")
    suggested_category_name = models.CharField(max_length=100, blank=True)

    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)

    source = models.CharField(max_length=100, db_index=True, help_text="e.g. OSM, Wikidata, Nepal_Govt_Gazetteer, Topo_Survey")
    source_url = models.URLField(max_length=500, blank=True)
    source_id = models.CharField(max_length=150, blank=True, db_index=True)
    evidence_data = models.JSONField(default=dict, blank=True, help_text="Raw source metadata, OSM tags, Wikidata claims, geocode proof")

    confidence_score = models.FloatField(default=0.0, help_text="0.0 to 100.0 confidence rating")
    quality_score = models.FloatField(default=0.0, help_text="0.0 to 100.0 completeness/quality score")

    discovery_status = models.CharField(
        max_length=50, choices=DiscoveryStatus.choices, default=DiscoveryStatus.DISCOVERED, db_index=True
    )
    duplicate_status = models.CharField(
        max_length=50, choices=DuplicateStatus.choices, default=DuplicateStatus.NONE, db_index=True
    )
    duplicate_reason = models.TextField(blank=True, help_text="Human-readable explanation of why this was or was not considered a duplicate")
    match_score = models.FloatField(default=0.0, help_text="Similarity percentage against best matched destination (0-100%)")
    matched_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="candidate_matches"
    )

    audit_trail = models.JSONField(default=list, blank=True, help_text="History of automated modifications, status changes, and promotions")

    class Meta:
        ordering = ["-quality_score", "-confidence_score", "name"]
        indexes = [
            models.Index(fields=["normalized_name", "district"]),
            models.Index(fields=["discovery_status", "quality_score"]),
            models.Index(fields=["source", "source_id"]),
            models.Index(fields=["place_type", "province"]),
        ]

    def __str__(self):
        return f"{self.name} [{self.place_type}] ({self.district}, {self.province}) — {self.discovery_status} ({self.quality_score:.0f}%)"


class DiscoveryJob(TimeStampedModel):
    """
    Tracks multi-source discovery batch jobs (resumable, district-by-district / province-by-province).
    """
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PAUSED = "paused", "Paused"

    job_id = models.CharField(max_length=100, unique=True, db_index=True)
    source_name = models.CharField(max_length=100)
    target_province = models.CharField(max_length=100, blank=True)
    target_district = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING, db_index=True)

    records_scanned = models.IntegerField(default=0)
    candidates_created = models.IntegerField(default=0)
    duplicates_found = models.IntegerField(default=0)
    verified_count = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)

    log_summary = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job {self.job_id} ({self.source_name} - {self.target_district or self.target_province or 'All Nepal'}) [{self.status}]"


class DestinationSourceField(TimeStampedModel):
    """
    Field-level provenance and verification tracking for all authoritative facts.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="field_sources")
    field_name = models.CharField(max_length=100, db_index=True, help_text="e.g. altitude, history, routes, permits")
    field_value = models.TextField()
    source_name = models.CharField(max_length=150)
    source_url = models.URLField(max_length=500, blank=True)
    source_id = models.CharField(max_length=150, blank=True)
    confidence = models.CharField(
        max_length=50, default="High",
        choices=[("High", "High"), ("Medium", "Medium"), ("Estimated", "Estimated"), ("Needs Review", "Needs Review")]
    )
    verification_status = models.CharField(
        max_length=50, default="Verified",
        choices=[("Verified", "Verified"), ("Estimated", "Estimated"), ("Pending", "Pending")]
    )
    last_verified = models.DateField(auto_now=True)

    class Meta:
        ordering = ["field_name"]

    def __str__(self):
        return f"{self.destination.name}.{self.field_name} = {self.field_value[:30]} ({self.source_name})"




# ===========================================================================
# AI Nepal Tourist Image Dataset Platform
# ===========================================================================

class ImageGenerationJob(TimeStampedModel):
    """One generation request for a destination (can produce many images)."""
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class Season(models.TextChoices):
        SPRING = "spring", "Spring"
        SUMMER = "summer", "Summer"
        AUTUMN = "autumn", "Autumn"
        WINTER = "winter", "Winter"

    class TimeOfDay(models.TextChoices):
        SUNRISE = "sunrise", "Sunrise"
        DAY = "day", "Daytime"
        SUNSET = "sunset", "Sunset"
        NIGHT = "night", "Night"

    class CameraStyle(models.TextChoices):
        LANDSCAPE = "landscape", "Landscape"
        AERIAL = "aerial", "Aerial / Drone"
        STREET = "street", "Street-level"
        ARCHITECTURAL = "architectural", "Architectural"
        CULTURAL = "cultural", "Cultural"
        TREKKING = "trekking", "Trekking"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="generation_jobs")
    provider = models.CharField(max_length=50, default="openai")
    model = models.CharField(max_length=100, blank=True)
    prompt = models.TextField()
    negative_prompt = models.TextField(blank=True)
    season = models.CharField(max_length=10, choices=Season.choices, default=Season.AUTUMN)
    time_of_day = models.CharField(max_length=10, choices=TimeOfDay.choices, default=TimeOfDay.DAY)
    camera_style = models.CharField(max_length=20, choices=CameraStyle.choices, default=CameraStyle.LANDSCAPE)
    num_images = models.PositiveSmallIntegerField(default=4)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    error_message = models.TextField(blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["destination", "status"])]

    def __str__(self):
        return f"Job {self.id} for {self.destination_id} ({self.status})"


class ImageTag(TimeStampedModel):
    image = models.ForeignKey(DestinationImage, on_delete=models.CASCADE, related_name="tags")
    tag = models.CharField(max_length=60, db_index=True)
    confidence = models.FloatField(default=1.0)

    class Meta:
        unique_together = ("image", "tag")
        indexes = [models.Index(fields=["tag"])]

    def __str__(self):
        return f"{self.tag} ({self.confidence:.2f})"


class ImageEmbedding(TimeStampedModel):
    """Vector embedding of an image / destination for semantic search."""
    class ContentType(models.TextChoices):
        IMAGE = "image", "Image"
        DESTINATION = "destination", "Destination text"

    image = models.OneToOneField(
        DestinationImage, on_delete=models.CASCADE, null=True, blank=True, related_name="embedding"
    )
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, null=True, blank=True, related_name="embeddings"
    )
    content_type = models.CharField(max_length=12, choices=ContentType.choices)
    embedding_model = models.CharField(max_length=60, default="clip-ViT-B-32")
    # Stored as JSON in SQLite (no pgvector dependency); adapter can swap to
    # pgvector on Postgres without touching calling code.
    vector = models.JSONField(default=list)
    dimensions = models.PositiveIntegerField(default=512)

    class Meta:
        indexes = [models.Index(fields=["content_type", "embedding_model"])]

    def __str__(self):
        return f"{self.content_type} embedding ({self.embedding_model})"


class DestinationReferenceImage(TimeStampedModel):
    """Authoritative reference photo used to validate generated output."""
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="reference_images")
    image_url = models.URLField(max_length=500)
    source = models.CharField(max_length=80, blank=True)
    license = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=300, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"ref for {self.destination_id}: {self.image_url[:60]}"


class InfrastructureSubmission(TimeStampedModel):
    """Community-supplied place/service data, published only after review."""

    class PlaceType(models.TextChoices):
        DESTINATION = "destination", "Tourism destination"
        HOTEL = "hotel", "Hotel / homestay"
        HOSPITAL = "hospital", "Hospital / clinic"
        POLICE = "police", "Police station"
        BANK = "bank", "Bank"
        ATM = "atm", "ATM"
        BLOOD_BANK = "blood_bank", "Blood bank"
        FIRE_STATION = "fire_station", "Fire station"
        AMBULANCE = "ambulance", "Ambulance service"
        TOURISM_OFFICE = "tourism_office", "Tourism office"
        PHARMACY = "pharmacy", "Pharmacy"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved and published"
        REJECTED = "rejected", "Rejected"
        NEEDS_CHANGES = "needs_changes", "Needs changes"

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="infrastructure_submissions",
    )
    place_type = models.CharField(max_length=30, choices=PlaceType.choices)
    name = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=120, blank=True)
    municipality = models.CharField(max_length=160, blank=True)
    municipality_type = models.CharField(
        max_length=30, blank=True,
        choices=[("metropolitan", "Metropolitan"), ("sub_metropolitan", "Sub-metropolitan"),
                 ("municipality", "Municipality"), ("rural_municipality", "Rural municipality")],
    )
    ward_number = models.PositiveSmallIntegerField(null=True, blank=True)
    district = models.CharField(max_length=120)
    province = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="infrastructure_submissions",
    )
    transport_mode = models.CharField(max_length=100, blank=True)
    route_origin = models.CharField(max_length=160, blank=True)
    travel_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    road_condition = models.CharField(max_length=160, blank=True)
    price_npr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    opening_hours = models.CharField(max_length=160, blank=True)
    image = models.ImageField(upload_to="community/services/images/", blank=True, null=True)
    video = models.FileField(upload_to="community/services/videos/", blank=True, null=True)
    source_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="infrastructure_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_model = models.CharField(max_length=60, blank=True)
    published_object_id = models.PositiveIntegerField(null=True, blank=True)
    csv_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "place_type"]), models.Index(fields=["latitude", "longitude"])]

    def __str__(self):
        return f"{self.get_place_type_display()}: {self.name} ({self.status})"


class InfrastructureMedia(TimeStampedModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    submission = models.ForeignKey(InfrastructureSubmission, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to="community/services/media/")
    caption = models.CharField(max_length=220, blank=True)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "created_at"]


class DestinationFeatureProfile(TimeStampedModel):
    """Structured, editable content features used alongside the existing recommender."""
    destination = models.OneToOneField(Destination, on_delete=models.CASCADE, related_name="feature_profile")
    difficulty = models.CharField(max_length=20, choices=[("easy", "Easy"), ("moderate", "Moderate"), ("hard", "Hard")], default="moderate")
    duration_days = models.PositiveSmallIntegerField(default=2)
    budget_level = models.CharField(max_length=20, choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium")
    nature_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    adventure_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    culture_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    spiritual_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    wildlife_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    photography_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    family_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    accessibility_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    source_type = models.CharField(max_length=30, default="admin")
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)


class RecommendationEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        IMPRESSION = "impression", "Recommendation impression"
        SELECT = "select", "Recommendation selected"
        SEARCH = "search", "Search"
        VIEW = "view", "Destination viewed"
        SAVE = "save", "Destination saved"
        RATING = "rating", "Rating"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="recommendation_events")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, null=True, blank=True, related_name="recommendation_events")
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    session_key = models.CharField(max_length=80, blank=True)
    query = models.CharField(max_length=300, blank=True)
    score = models.FloatField(null=True, blank=True)
    context = models.JSONField(default=dict, blank=True)
    consented = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "event_type", "created_at"]), models.Index(fields=["destination", "event_type"])]


class RiskObservation(TimeStampedModel):
    class ObservationType(models.TextChoices):
        RAINFALL = "rainfall", "Rainfall"
        RIVER_LEVEL = "river_level", "River level"
        TEMPERATURE = "temperature", "Temperature"
        WIND = "wind", "Wind"
        SNOW = "snow", "Snow"
        WARNING_LEVEL = "warning_level", "Warning level"
        OTHER = "other", "Other"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="risk_observations")
    observation_type = models.CharField(max_length=30, choices=ObservationType.choices)
    value = models.FloatField()
    unit = models.CharField(max_length=30)
    trend = models.CharField(max_length=30, blank=True, choices=[("rising", "Rising"), ("falling", "Falling"), ("steady", "Steady"), ("unknown", "Unknown")])
    station_name = models.CharField(max_length=180)
    station_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    station_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    source_type = models.CharField(max_length=30, default="official")
    source_name = models.CharField(max_length=180)
    source_url = models.URLField(max_length=600, blank=True)
    observed_at = models.DateTimeField()
    published_at = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-observed_at"]
        indexes = [models.Index(fields=["destination", "observation_type", "observed_at"])]


class RiskNewsReport(TimeStampedModel):
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="risk_news")
    title = models.CharField(max_length=260)
    summary = models.TextField(blank=True)
    hazard_type = models.CharField(max_length=30, choices=RiskIncident.HazardType.choices, default=RiskIncident.HazardType.OTHER)
    source_name = models.CharField(max_length=180)
    source_url = models.URLField(max_length=600, unique=True)
    published_at = models.DateTimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    affected_area = models.CharField(max_length=240, blank=True)
    verification_status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected"), ("outdated", "Outdated")], default="pending")
    promoted_to_warning = models.BooleanField(default=False, help_text="Requires a separate verified Alert; news alone is never an official warning")

    class Meta:
        ordering = ["-published_at"]
        indexes = [models.Index(fields=["destination", "verification_status", "published_at"])]


class MLTrainingRun(TimeStampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    model_type = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    version = models.CharField(max_length=80)
    previous_version = models.CharField(max_length=80, blank=True)
    dataset_size = models.PositiveIntegerField(default=0)
    newly_approved_records = models.PositiveIntegerField(default=0)
    validation_metrics = models.JSONField(default=dict, blank=True)
    output_log = models.TextField(blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ml_training_runs")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["model_type", "status", "created_at"])]


class UserFeedback(TimeStampedModel):
    """Direct messages / feedback from a user to the admin team."""
    class Status(models.TextChoices):
        NEW = "new", "New"
        READ = "read", "Read"
        IN_PROGRESS = "in_progress", "In Progress"
        WAITING_USER = "waiting_user", "Waiting for User"
        REPLIED = "replied", "Replied"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks",
        null=True, blank=True,
    )
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=50, default="general")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=10, choices=[("low","Low"),("normal","Normal"),("high","High"),("urgent","Urgent")], default="normal", db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_feedback_threads")
    last_user_read_at = models.DateTimeField(null=True, blank=True)
    last_staff_read_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    admin_reply = models.TextField(blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="feedback_replies",
    )
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["category"])]

    def __str__(self):
        return f"{self.subject} ({self.status})"


class FeedbackEvidence(TimeStampedModel):
    feedback = models.ForeignKey(UserFeedback, on_delete=models.CASCADE, related_name="evidence")
    media_type = models.CharField(max_length=10, choices=[("image", "Image"), ("video", "Video")])
    file = models.FileField(upload_to="feedback/evidence/")
    caption = models.CharField(max_length=220, blank=True)
    is_verified = models.BooleanField(default=False)


class SiteSetting(TimeStampedModel):
    key = models.SlugField(max_length=120, unique=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True)
    is_public = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="site_settings_updated")

    def __str__(self): return self.key


class BrandingAsset(TimeStampedModel):
    class Kind(models.TextChoices):
        LOGO = "logo", "Logo"
        FAVICON = "favicon", "Favicon"

    kind = models.CharField(max_length=20, choices=Kind.choices, unique=True)
    file = models.ImageField(upload_to="branding/")
    alt_text = models.CharField(max_length=160, blank=True)
    mime_type = models.CharField(max_length=80, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="branding_assets_updated")

    def __str__(self): return self.kind


class CMSContentTranslation(TimeStampedModel):
    target_resource = models.CharField(max_length=20, choices=[("pages", "Page"), ("sections", "Section"), ("navigation", "Navigation")])
    object_id = models.PositiveBigIntegerField()
    language_code = models.CharField(max_length=10)
    content = models.JSONField(default=dict)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="cms_translations_updated")

    class Meta:
        ordering = ["target_resource", "object_id", "language_code"]
        constraints = [models.UniqueConstraint(fields=["target_resource", "object_id", "language_code"], name="unique_cms_content_translation")]
        indexes = [models.Index(fields=["target_resource", "object_id", "language_code"])]


class ManagedPage(TimeStampedModel):
    route = models.CharField(max_length=180, unique=True)
    key = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=220)
    meta_description = models.CharField(max_length=320, blank=True)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=[("draft","Draft"),("scheduled","Scheduled"),("published","Published")], default="published")
    scheduled_publish_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_pages_updated")

    def __str__(self): return f"{self.title} ({self.route})"


class ContentSection(TimeStampedModel):
    page = models.ForeignKey(ManagedPage, on_delete=models.CASCADE, related_name="sections")
    key = models.SlugField(max_length=120)
    title = models.CharField(max_length=240, blank=True)
    subtitle = models.CharField(max_length=320, blank=True)
    body = models.TextField(blank=True)
    image_url = models.URLField(max_length=600, blank=True)
    cta_text = models.CharField(max_length=100, blank=True)
    cta_url = models.CharField(max_length=240, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    layout_variant = models.CharField(max_length=30, choices=[("default","Default"),("compact","Compact"),("wide","Wide"),("cards","Cards")], default="default")
    config = models.JSONField(default=dict, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=[("draft","Draft"),("scheduled","Scheduled"),("published","Published")], default="published")
    scheduled_publish_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="content_sections_updated")

    class Meta:
        ordering = ["display_order", "id"]
        constraints = [models.UniqueConstraint(fields=["page","key"], name="unique_page_section_key")]


class ManagedNavigationItem(TimeStampedModel):
    location = models.CharField(max_length=20, choices=[("navbar","Navbar"),("sidebar","Sidebar"),("footer","Footer")])
    label = models.CharField(max_length=120)
    route = models.CharField(max_length=240)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    allowed_roles = models.JSONField(default=list, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="navigation_items_updated")

    class Meta:
        ordering = ["location", "display_order", "id"]


class CMSRevision(models.Model):
    """Immutable snapshots for safe CMS preview, audit, and rollback."""
    resource = models.CharField(max_length=20, choices=[("pages", "Pages"), ("sections", "Sections"), ("navigation", "Navigation"), ("settings", "Settings"), ("translations", "Translations")])
    object_id = models.PositiveBigIntegerField()
    revision_number = models.PositiveIntegerField()
    snapshot = models.JSONField(default=dict)
    action = models.CharField(max_length=20, choices=[("create", "Create"), ("update", "Update"), ("publish", "Publish"), ("unpublish", "Unpublish"), ("schedule", "Schedule"), ("rollback", "Rollback")])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="cms_revisions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-revision_number"]
        constraints = [models.UniqueConstraint(fields=["resource", "object_id", "revision_number"], name="unique_cms_object_revision")]
        indexes = [models.Index(fields=["resource", "object_id", "-revision_number"])]


class FeedbackMessage(TimeStampedModel):
    feedback = models.ForeignKey(UserFeedback, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="feedback_messages")
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="feedback/messages/", blank=True, null=True)
