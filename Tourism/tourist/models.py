import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
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
    deactivated_at = models.DateTimeField(null=True, blank=True)
    anonymized_at = models.DateTimeField(null=True, blank=True)
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
    MODULES = ["dashboard", "tasks", "support", "destinations", "images", "content", "budget", "datasets", "hotels", "restaurants", "transportation", "travel_plans", "reviews", "safety", "feedback", "audit", "users", "settings", "marketplace"]
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
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted for Review"
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

    coordinate_source = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Origin source for GPS coordinates (e.g. Official Survey, OSM, Admin Verified).",
    )

    coordinate_accuracy = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Accuracy level (e.g. High / Exact, Moderate, District Center).",
    )

    coordinate_status = models.CharField(
        max_length=30,
        choices=[
            ("VERIFIED", "Verified"),
            ("OFFICIAL", "Official"),
            ("COMMUNITY_VERIFIED", "Community Verified"),
            ("APPROXIMATE", "Approximate"),
            ("UNVERIFIED", "Unverified"),
            ("NOT_RECORDED", "Not Recorded"),
        ],
        default="UNVERIFIED",
        db_index=True,
    )

    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_destinations",
    )
    location_notes = models.TextField(blank=True)
    locality = models.CharField(max_length=100, blank=True)


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

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="destination_submissions",
        help_text="Staff member who created/submitted this entry for review."
    )


    is_active = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False,
        help_text="Pinned by an administrator for the homepage and traveller dashboard.",
    )

    ai_recommendation_status = models.CharField(
        max_length=20,
        choices=[("ALLOWED", "Allowed"), ("BLOCKED", "Blocked"), ("PRIORITY", "Priority")],
        default="ALLOWED",
        db_index=True,
    )
    ai_priority_level = models.CharField(
        max_length=20,
        choices=[("LOW", "Low"), ("NORMAL", "Normal"), ("HIGH", "High"), ("CRITICAL", "Critical")],
        default="NORMAL",
    )
    ai_override_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["city", "country"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_featured", "is_active"]),
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
    crop_box = models.JSONField(default=dict, blank=True, help_text='Optional focal crop as {"x":0,"y":0,"w":100,"h":100} percentages.')

    class Meta:
        ordering = ["-is_cover", "ordering", "-is_promoted", "-view_count", "-created_at"]
        indexes = [
            models.Index(fields=["destination", "ordering"], name="destimg_dest_order_idx"),
            models.Index(fields=["image_path"], name="destimg_path_idx"),
        ]

    def __str__(self):
        return f"{self.destination.name} photo ({self.get_source_display()})"


class DestinationVideo(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="videos")
    video_url = models.URLField(blank=True, help_text="YouTube/Vimeo link or hosted video URL")
    video_file = models.FileField(upload_to="destinations/videos/", blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    thumbnail = models.ImageField(upload_to="destinations/video_thumbnails/", blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_videos"
    )
    verification_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)


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


class UserRoute(TimeStampedModel):
    """A calculated route for a traveller: navigation history + saved routes.

    Every successfully calculated route by a signed-in user is logged here
    (history); starring a route flips `is_saved` so it persists in the
    traveller's Saved Routes list (spec items 15/16). Distances/durations
    store what the routing layer actually returned, with its source label —
    never a re-derived or invented number.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes")
    origin_name = models.CharField(max_length=200, blank=True)
    origin_latitude = models.FloatField(null=True, blank=True)
    origin_longitude = models.FloatField(null=True, blank=True)
    destination_name = models.CharField(max_length=200)
    destination_latitude = models.FloatField(null=True, blank=True)
    destination_longitude = models.FloatField(null=True, blank=True)
    transport_mode = models.CharField(max_length=60, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    duration_min = models.IntegerField(null=True, blank=True)
    duration_source = models.CharField(max_length=20, blank=True, help_text="routing_engine | estimated | unavailable")
    label = models.CharField(max_length=200, blank=True, help_text="Optional traveller label, e.g. 'Home → Work'")
    is_saved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_saved"])]


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
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)

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
    is_archived = models.BooleanField(default=False)
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
    is_archived = models.BooleanField(default=False)
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
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

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
        REVOKED = "revoked", "Revoked"

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
        # Tourism-service categories added for the OSM import pipeline
        # (import_osm_services). Extending choices is a schema no-op but keeps
        # validation + admin pickers in sync with what real OSM data carries.
        RESTAURANT = "restaurant", "Restaurant"
        CAFE = "cafe", "Cafe"
        FAST_FOOD = "fast_food", "Fast Food"
        BAKERY = "bakery", "Bakery"
        BAR = "bar", "Bar / Pub"
        DOCTORS = "doctors", "Doctors"
        DENTIST = "dentist", "Dentist"
        FUEL = "fuel", "Fuel Station"
        BUS_STATION = "bus_station", "Bus Station"
        TAXI = "taxi", "Taxi"
        SUPERMARKET = "supermarket", "Supermarket"
        MARKETPLACE = "marketplace", "Marketplace"
        CHARGING_STATION = "charging_station", "EV Charging Station"
        GUEST_HOUSE = "guest_house", "Guest House / Hostel"

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
    is_archived = models.BooleanField(default=False)
    opening_hours = models.CharField(max_length=160, blank=True)
    emergency_available = models.BooleanField(default=False)
    raw_tags = models.JSONField(default=dict, blank=True)

    # --- Trust state (§6): OSM imports are NEVER automatically authoritative.
    class VerificationState(models.TextChoices):
        IMPORTED = "imported", "Imported from OSM (unverified)"
        SOURCE_VERIFIED = "source_verified", "Cross-checked against source extract"
        ADMIN_REVIEW = "admin_review", "Queued for admin review"
        VERIFIED = "verified", "Admin verified (authoritative)"
        REJECTED = "rejected", "Rejected / stale"

    verification_state = models.CharField(
        max_length=20, choices=VerificationState.choices,
        default=VerificationState.IMPORTED, db_index=True,
        help_text="Only admin action may set VERIFIED/REJECTED; imports stay IMPORTED.")
    last_enriched_at = models.DateTimeField(
        null=True, blank=True, help_text="When OSM tags were last re-read into this row.")
    # --- Enrichment fields (§2): populated only from real OSM tags, never invented.
    name_en = models.CharField(max_length=255, blank=True)
    name_ne = models.CharField(max_length=255, blank=True)
    website = models.URLField(max_length=600, blank=True)
    operator = models.CharField(max_length=180, blank=True)

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


class Restaurant(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="restaurants")
    name = models.CharField(max_length=220)
    cuisine_types = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=60, blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)
    price_range = models.CharField(max_length=10, choices=[("budget", "Budget"), ("mid", "Mid-range"), ("premium", "Premium")], default="mid")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    vegetarian_friendly = models.BooleanField(default=False)
    image_url = models.URLField(max_length=600, blank=True)
    source_name = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(max_length=600, blank=True)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="restaurants_updated")

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["destination", "name"], name="unique_restaurant_destination_name")]

    def __str__(self): return f"{self.name} ({self.destination.name})"


class DestinationTransitRoute(TimeStampedModel):
    """Available transportation options, routes, conditions, and fares."""
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="transit_routes")
    origin = models.CharField(max_length=150, help_text="e.g. Kathmandu (Kalanki) / Pokhara / Nearest Airport")
    origin_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    origin_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    transport_mode = models.CharField(max_length=100, default="Public Deluxe Bus")
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    approx_duration = models.CharField(max_length=100, help_text="e.g. 5 hours 30 mins")
    road_condition = models.CharField(max_length=150, blank=True, default="Paved Highway")
    key_stops = models.TextField(blank=True, help_text="Major transit waypoints along the route")
    estimated_fare_npr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fare_currency = models.CharField(max_length=10, default="NPR")
    route_source = models.CharField(max_length=200, blank=True, default="Nepal Highway Authority & Local Transit")
    operator_name = models.CharField(max_length=180, blank=True)
    contact_phone = models.CharField(max_length=60, blank=True)
    booking_url = models.URLField(max_length=600, blank=True)
    departure_schedule = models.CharField(max_length=200, blank=True)

    confidence_level = models.CharField(
        max_length=30,
        choices=[
            ("VERIFIED", "Verified"),
            ("OFFICIAL", "Official"),
            ("ADMIN_VERIFIED", "Admin Verified"),
            ("PROVIDER_DATA", "Provider Data"),
            ("CALCULATED", "Calculated"),
            ("ESTIMATED", "Estimated"),
            ("UNVERIFIED", "Unverified"),
            ("UNKNOWN", "Unknown"),
        ],
        default="CALCULATED",
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="transit_routes_updated")

    class Meta:
        ordering = ["distance_km", "-updated_at"]

    def __str__(self):
        return f"{self.origin} ➔ {self.destination.name} via {self.transport_mode}"


class RouteSegment(TimeStampedModel):
    """Segment breakdown for multi-leg journeys across Nepal."""
    route = models.ForeignKey(DestinationTransitRoute, on_delete=models.CASCADE, related_name="segments")
    segment_order = models.PositiveSmallIntegerField(default=1)
    from_location = models.CharField(max_length=200)
    to_location = models.CharField(max_length=200)
    transport_mode = models.CharField(max_length=100, default="Local Bus")
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    duration_mins = models.PositiveIntegerField(null=True, blank=True)
    fare_npr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["route", "segment_order"]

    def __str__(self):
        return f"Leg {self.segment_order}: {self.from_location} ➔ {self.to_location} ({self.transport_mode})"


class DataReport(TimeStampedModel):
    """User error reporting and data quality correction queue."""

    class ReportType(models.TextChoices):
        MAP_LOCATION = "map_location", "Wrong Map Location"
        ROUTE = "route", "Wrong Route"
        DISTANCE = "distance", "Wrong Distance"
        TRAVEL_TIME = "travel_time", "Wrong Travel Time"
        FARE = "fare", "Wrong Fare / Price"
        OPENING_HOURS = "opening_hours", "Wrong Opening Hours"
        PHOTO = "photo", "Wrong or Broken Photo"
        DESCRIPTION = "description", "Wrong Description"
        MOVED = "moved", "Destination Moved or Closed"
        SAFETY = "safety", "Incorrect Safety Advice"
        OTHER = "other", "Other Data Correction"

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        NEW = "new", "New Report"
        UNDER_REVIEW = "under_review", "Under Review"
        NEEDS_VERIFICATION = "needs_verification", "Needs Verification"
        FIXED = "fixed", "Fixed & Verified"
        REJECTED = "rejected", "Rejected"
        DUPLICATE = "duplicate", "Duplicate"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="data_reports",
    )
    destination = models.ForeignKey(
        Destination, null=True, blank=True, on_delete=models.CASCADE, related_name="data_reports",
    )
    route = models.ForeignKey(
        DestinationTransitRoute, null=True, blank=True, on_delete=models.SET_NULL, related_name="data_reports",
    )
    report_type = models.CharField(max_length=30, choices=ReportType.choices, default=ReportType.OTHER, db_index=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)

    page_url = models.CharField(max_length=500, blank=True)
    field_name = models.CharField(max_length=100, blank=True)
    displayed_value = models.TextField(blank=True)
    suggested_value = models.TextField(blank=True)
    description = models.TextField(blank=True)

    internal_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="data_reports_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["report_type", "status"]),
        ]

    def __str__(self):
        dest = self.destination.name if self.destination else "General"
        return f"[{self.get_severity_display()}] {self.get_report_type_display()} on {dest} ({self.get_status_display()})"


class TravelPlan(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="travel_plans")
    title = models.CharField(max_length=220)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    travelers = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(50)])
    budget_npr = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    interests = models.JSONField(default=list, blank=True)
    itinerary_data = models.JSONField(default=dict, blank=True)
    generation_source = models.CharField(max_length=20, choices=[("manual", "Manual"), ("ml", "ML assisted")], default="manual")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date")

    def __str__(self): return f"{self.title} — {self.user.email}"


class TravelPlanStop(TimeStampedModel):
    plan = models.ForeignKey(TravelPlan, on_delete=models.CASCADE, related_name="stops")
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name="travel_plan_stops")
    transit_route = models.ForeignKey(DestinationTransitRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name="plan_stops")
    day_number = models.PositiveSmallIntegerField(default=1)
    display_order = models.PositiveSmallIntegerField(default=0)
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["day_number", "display_order", "id"]
        constraints = [models.UniqueConstraint(fields=["plan", "day_number", "display_order"], name="unique_plan_day_stop_order")]


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
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

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


class UserPreferenceProfile(TimeStampedModel):
    """Dynamic user preference weights derived from interactions & survey inputs."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference_profile")

    culture_weight = models.FloatField(default=0.5)
    trekking_weight = models.FloatField(default=0.5)
    nature_weight = models.FloatField(default=0.5)
    adventure_weight = models.FloatField(default=0.5)
    spiritual_weight = models.FloatField(default=0.5)
    wildlife_weight = models.FloatField(default=0.5)
    photography_weight = models.FloatField(default=0.5)
    relaxation_weight = models.FloatField(default=0.5)
    food_weight = models.FloatField(default=0.5)
    family_weight = models.FloatField(default=0.5)

    budget_sensitivity = models.FloatField(default=0.5)
    pace_preference = models.CharField(max_length=20, default="balanced")
    exploration_mode = models.CharField(max_length=20, default="balanced")

    preferred_provinces = models.JSONField(default=list, blank=True)
    visited_destination_ids = models.JSONField(default=list, blank=True)
    avoid_destination_ids = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Preferences for {self.user.email}"


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
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    recommendation_quality_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    itinerary_quality_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    budget_accuracy_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    route_quality_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    destination = models.ForeignKey(Destination, null=True, blank=True, on_delete=models.SET_NULL, related_name="user_feedbacks")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=10, choices=[("low","Low"),("normal","Normal"),("high","High"),("urgent","Urgent")], default="normal", db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_feedback_threads")
    last_user_read_at = models.DateTimeField(null=True, blank=True)
    last_staff_read_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    # Escalation (Staff Ops spec §10): staff flag tickets they cannot solve.
    is_escalated = models.BooleanField(default=False, db_index=True)
    escalation_reason = models.TextField(blank=True)
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


class DataRetentionPolicy(TimeStampedModel):
    """Singleton operational retention windows for ephemeral personal data."""
    name = models.CharField(max_length=80, unique=True, default="default")
    read_notification_days = models.PositiveIntegerField(default=365, validators=[MinValueValidator(30), MaxValueValidator(3650)])
    location_ping_days = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1), MaxValueValidator(365)])
    recommendation_event_days = models.PositiveIntegerField(default=365, validators=[MinValueValidator(30), MaxValueValidator(3650)])
    resolved_sos_days = models.PositiveIntegerField(default=730, validators=[MinValueValidator(365), MaxValueValidator(3650)])
    audit_log_days = models.PositiveIntegerField(default=2555, validators=[MinValueValidator(365), MaxValueValidator(7300)])
    preserve_official_risk_records = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="retention_policies_updated")

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.preserve_official_risk_records:
            raise ValidationError("Official risk records are safety-critical and must be preserved")

    def __str__(self): return self.name


class MunicipalityMapping(TimeStampedModel):
    """Maps municipality/local-level names to canonical district + province.

    Populated three ways: admin CSV import (verified), admin manual entry
    (verified), or coordinate-derived candidates from destination clusters
    (unverified until an admin confirms). Never fabricated.
    """

    SOURCE_CHOICES = [
        ("csv_import", "Admin CSV import"),
        ("admin", "Admin manual"),
        ("coordinate_derived", "Coordinate-derived candidate"),
    ]
    name = models.CharField(max_length=180, unique=True)
    district = models.CharField(max_length=100)
    province = models.CharField(max_length=60)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default="admin")
    verified = models.BooleanField(default=False)
    matched_destination_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} -> {self.district}, {self.province}"


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


class HeroSlide(TimeStampedModel):
    """A single, admin-managed cinematic landing hero slide.

    Administrators can upload a photo, paste an absolute URL, or point at a
    bundled ``/images/...`` asset; swap copy; tune the legibility overlay and
    focal point; and reorder / enable slides. The public config serializes the
    resolved image so the frontend never has to guess. See
    :class:`HeroSlide.resolve_image`.
    """

    class FocalPoint(models.TextChoices):
        CENTER = "center", "Center"
        TOP = "top", "Top (sky / peaks)"
        BOTTOM = "bottom", "Bottom (valley / foreground)"

    title = models.CharField(max_length=120)
    kicker = models.CharField(max_length=140, blank=True, help_text="Small pill line, e.g. “Solukhumbu · 8,849 m”")
    subtitle = models.CharField(max_length=200, blank=True)
    tagline = models.CharField(max_length=300, blank=True)
    link_slug = models.SlugField(max_length=140, blank=True, help_text="Destination slug for the primary Explore button")

    image = models.ImageField(upload_to="hero/", blank=True, help_text="Uploaded photo (served from /media/).")
    image_url = models.URLField(max_length=600, blank=True, help_text="Absolute CDN / Wikimedia URL, used if no upload.")
    local_image = models.CharField(max_length=300, blank=True, help_text="Bundled asset path e.g. /images/destinations/everest/base-camp.jpg")

    overlay_strength = models.PositiveSmallIntegerField(default=60, validators=[MinValueValidator(10), MaxValueValidator(92)], help_text="Legibility scrim intensity in percent. Higher = darker, more readable text.")
    focal_point = models.CharField(max_length=10, choices=FocalPoint.choices, default=FocalPoint.CENTER)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    duration_seconds = models.PositiveSmallIntegerField(default=7, validators=[MinValueValidator(3), MaxValueValidator(20)])
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="hero_slides_updated")

    class Meta:
        ordering = ["order", "id"]

    def resolve_image(self, request=None):
        if self.image:
            return self.image.url
        return self.image_url or self.local_image

    def __str__(self): return f"{self.order}. {self.title}"


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
    seo_title = models.CharField(max_length=70, blank=True, help_text="Optional search-result title. Blank uses the page title.")
    og_image_url = models.URLField(max_length=600, blank=True)
    search_visible = models.BooleanField(default=True)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=[("draft","Draft"),("in_review","In Review"),("changes_requested","Changes Requested"),("approved","Approved"),("scheduled","Scheduled"),("published","Published")], default="published")
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
    section_type = models.CharField(
        max_length=30,
        choices=[
            ("text", "Text"), ("heading", "Heading"), ("image", "Image"), ("gallery", "Gallery"),
            ("cards", "Cards"), ("faq", "FAQ"), ("cta", "Call to action"), ("map", "Map"),
            ("video", "Video"), ("audio", "Audio"), ("marquee", "Marquee"),
            ("animation", "Animation"), ("media", "Media"), ("form", "Form"),
            ("table", "Table"), ("figure", "Figure"), ("testimonials", "Testimonials"),
            ("contact", "Contact"), ("breadcrumbs", "Breadcrumbs"), ("search", "Search"),
            ("blocks", "Block Container"),
        ],
        default="text",
    )
    layout_variant = models.CharField(
        max_length=30,
        choices=[
            ("default", "Default"), ("compact", "Compact"), ("wide", "Wide"),
            ("cards", "Cards"), ("hero", "Hero"), ("split", "Split"),
        ],
        default="default",
    )
    config = models.JSONField(default=dict, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    is_reusable = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[("draft","Draft"),("in_review","In Review"),("changes_requested","Changes Requested"),("approved","Approved"),("scheduled","Scheduled"),("published","Published")], default="published")
    scheduled_publish_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    published_snapshot = models.JSONField(
        null=True, blank=True,
        help_text="Frozen content the public site serves. Edits write the live "
                  "(draft) fields; Publish copies them here so drafts never leak.")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="content_sections_updated")

    class Meta:
        ordering = ["display_order", "id"]
        constraints = [models.UniqueConstraint(fields=["page","key"], name="unique_page_section_key")]


class ContentBlock(TimeStampedModel):
    """
    Flexible block-based CMS element belonging to a ContentSection.
    Supports structured blocks: heading, rich_text, image, gallery, button,
    table, video, map, destination_grid, hotel_grid, restaurant_grid,
    statistics, list, quote, alert, divider, html.
    """
    section = models.ForeignKey(ContentSection, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(
        max_length=50,
        choices=[
            ("heading", "Heading"), ("subheading", "Subheading"), ("rich_text", "Rich Text"),
            ("image", "Image"), ("gallery", "Gallery"), ("button", "Button"),
            ("table", "Table"), ("video", "Video / Iframe"), ("map", "Map"),
            ("destination_grid", "Destination Grid"), ("hotel_grid", "Hotel Grid"),
            ("restaurant_grid", "Restaurant Grid"), ("statistics", "Statistics"),
            ("list", "List"), ("quote", "Quote"), ("alert", "Alert / Callout"),
            ("divider", "Divider"), ("html", "Custom Safe HTML"),
            ("card_grid", "Card Grid"), ("packages", "Travel Packages Grid"),
        ],
        default="rich_text",
    )
    title = models.CharField(max_length=240, blank=True)
    position = models.PositiveIntegerField(default=0)
    data = models.JSONField(default=dict, blank=True)
    is_visible = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="content_blocks_updated")

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.block_type} (#{self.id}) in {self.section.key}"


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


class NewsletterSignup(TimeStampedModel):
    """Footer newsletter signups. Admins browse/export via the Data Explorer."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class RedirectRule(TimeStampedModel):
    """Admin-managed URL redirects (old path -> new path).

    Exposed through the public config so the SPA can move visitors from
    renamed/retired URLs to their new home without a redeploy."""

    old_path = models.CharField(max_length=240, unique=True, help_text="Path to redirect from, e.g. /destinations/everest-old")
    new_path = models.CharField(max_length=240, help_text="Path (or https:// URL) to redirect to")
    is_permanent = models.BooleanField(default=True, help_text="Permanent (301-style) vs temporary redirect")
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=240, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="redirect_rules_updated")

    class Meta:
        ordering = ["-updated_at", "id"]

    def __str__(self):
        return f"{self.old_path} -> {self.new_path}"


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


class VisitorNotice(TimeStampedModel):
    """Organisation-published visitor bulletin: festivals, closures, permits, seasonal notes."""

    class Kind(models.TextChoices):
        FESTIVAL = "festival", "Festival"
        CLOSURE = "closure", "Closure"
        PERMIT = "permit", "Permit"
        SEASONAL = "seasonal", "Seasonal"
        CROWD = "crowd", "Crowd"
        TRANSPORT = "transport", "Transport"
        INFO = "info", "Information"

    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.INFO, db_index=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="visitor_notices",
    )
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="visitor_notices_updated",
    )

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["is_published", "starts_at", "ends_at"]),
            models.Index(fields=["kind", "is_published"]),
        ]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.title}"


class FeaturedDestination(TimeStampedModel):
    """Admin Content Publishing Studio: Promotional configuration for featured destinations."""

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="featured_configurations",
        help_text="The underlying destination record being promoted.",
    )
    title = models.CharField(
        max_length=240,
        blank=True,
        help_text="Custom promotional title for the card. Blank defaults to destination name.",
    )
    short_description = models.TextField(
        blank=True,
        help_text="Custom promotional description. Blank defaults to destination description.",
    )
    featured_media = models.ForeignKey(
        DestinationImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_promotions",
        help_text="Selected verified media record from destination gallery.",
    )
    featured_media_url = models.URLField(
        max_length=600,
        blank=True,
        help_text="Direct image URL override or fallback.",
    )
    cta_label = models.CharField(
        max_length=60,
        default="Explore Destination",
        help_text="Button text for call-to-action.",
    )
    cta_url = models.CharField(
        max_length=240,
        blank=True,
        help_text="Custom internal path override (e.g., /destinations/pokhara). Blank defaults to destination route.",
    )
    display_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Ordering position in featured carousel/grid.",
    )
    is_published = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Publishing status toggle.",
    )
    publish_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional start time for scheduled publishing.",
    )
    publish_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional end time for scheduled publishing.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="featured_destinations_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="featured_destinations_updated",
    )

    class Meta:
        ordering = ["display_order", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["destination"],
                name="unique_featured_destination_ref",
            )
        ]
        indexes = [
            models.Index(fields=["is_published", "display_order"]),
            models.Index(fields=["publish_start", "publish_end"]),
        ]

    def __str__(self):
        return f"Featured: {self.title or self.destination.name} (Order: {self.display_order})"

    @property
    def effective_title(self):
        return self.title.strip() if self.title and self.title.strip() else self.destination.name

    @property
    def effective_description(self):
        if self.short_description and self.short_description.strip():
            return self.short_description.strip()
        return self.destination.short_description or self.destination.description or ""

    @property
    def effective_image_url(self):
        if self.featured_media_url and self.featured_media_url.strip():
            return self.featured_media_url.strip()
        if self.featured_media:
            if self.featured_media.image:
                try:
                    return self.featured_media.image.url
                except (ValueError, AttributeError):
                    pass
            if self.featured_media.external_url:
                return self.featured_media.external_url
        if self.destination.cover_image:
            try:
                return self.destination.cover_image.url
            except (ValueError, AttributeError):
                return str(self.destination.cover_image)
        return getattr(self.destination, "external_image_url", "") or ""

    @property
    def effective_cta_url(self):
        if self.cta_url and self.cta_url.strip():
            return self.cta_url.strip()
        return f"/destinations/{self.destination.slug}"


class MarketplacePartner(TimeStampedModel):
    """Hotel, operator, restaurant or agency that wants to sell through this platform."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    class Kind(models.TextChoices):
        HOTEL = "hotel", "Hotel / stay"
        HOMESTAY = "homestay", "Homestay"
        OPERATOR = "operator", "Tour operator"
        GUIDE = "guide", "Local guide"
        RESTAURANT = "restaurant", "Restaurant"
        TRANSPORT = "transport", "Transport"
        ACTIVITY = "activity", "Activity provider"
        AGENCY = "agency", "Travel agency"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OPERATOR)
    contact_name = models.CharField(max_length=160, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    website = models.URLField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    services = models.TextField(blank=True, help_text="Packages or services the partner wants to list.")
    license_info = models.CharField(max_length=240, blank=True)
    logo_url = models.URLField(max_length=600, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="marketplace_partners",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="marketplace_partners_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.status})"


class MarketplaceListing(TimeStampedModel):
    """Admin- or partner-managed package, stay, tour, transfer or sponsored offer."""

    class Kind(models.TextChoices):
        PACKAGE = "package", "Travel package"
        HOTEL = "hotel", "Hotel / stay"
        TOUR = "tour", "Tour / sightseeing"
        ACTIVITY = "activity", "Activity"
        TRANSFER = "transfer", "Transfer / transport"
        RESTAURANT = "restaurant", "Food experience"
        GUIDE = "guide", "Guide"
        AD = "ad", "Sponsored offer"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    partner = models.ForeignKey(MarketplacePartner, on_delete=models.CASCADE, related_name="listings")
    destination = models.ForeignKey(Destination, null=True, blank=True, on_delete=models.SET_NULL, related_name="marketplace_listings")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.PACKAGE, db_index=True)
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    summary = models.CharField(max_length=320, blank=True)
    description = models.TextField(blank=True)
    includes = models.TextField(blank=True)
    excludes = models.TextField(blank=True)
    duration_days = models.PositiveSmallIntegerField(default=1)
    price_npr = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="NPR")
    image_url = models.URLField(max_length=600, blank=True)
    external_url = models.URLField(max_length=600, blank=True, help_text="Partner booking page. Must be HTTPS.")
    city = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    cancellation_policy = models.CharField(max_length=320, blank=True)
    capacity = models.PositiveIntegerField(default=10)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="marketplace_listings_updated",
    )

    class Meta:
        ordering = ["-is_featured", "-updated_at"]
        indexes = [models.Index(fields=["status", "kind"]), models.Index(fields=["is_featured", "status"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "offer"
            slug = base
            n = 2
            while MarketplaceListing.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class MarketplaceOrder(TimeStampedModel):
    """Trip basket / checkout. Never stores card numbers."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Trip basket"
        REQUESTED = "requested", "Requested"
        UNDER_REVIEW = "under_review", "Under review"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        EXTERNAL = "external", "Sent to partner site"

    class PayMethod(models.TextChoices):
        REQUEST = "request", "Request to book (pay later / with operator)"
        EXTERNAL = "external", "Continue on partner website"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="marketplace_orders",
    )
    reference = models.CharField(max_length=20, unique=True, blank=True)
    guest_name = models.CharField(max_length=160, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=40, blank=True)
    travelers = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    payment_method = models.CharField(max_length=20, choices=PayMethod.choices, default=PayMethod.REQUEST)
    subtotal_npr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_npr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="NPR")

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"NP{timezone.now().strftime('%y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def recompute(self):
        total = sum((item.line_total_npr or 0) for item in self.items.all())
        self.subtotal_npr = total
        self.total_npr = total
        self.save(update_fields=["subtotal_npr", "total_npr", "updated_at"])


class MarketplaceOrderItem(TimeStampedModel):
    order = models.ForeignKey(MarketplaceOrder, on_delete=models.CASCADE, related_name="items")
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.PROTECT, related_name="order_items")
    title = models.CharField(max_length=220)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price_npr = models.DecimalField(max_digits=12, decimal_places=2)
    line_total_npr = models.DecimalField(max_digits=12, decimal_places=2)
    travel_date = models.DateField(null=True, blank=True)
    external_url = models.URLField(max_length=600, blank=True)

    def __str__(self):
        return f"{self.title} × {self.quantity}"


class TravelerDocument(TimeStampedModel):
    """Travel documents / IDs for the account owner and their companions.

    Powers the Personal Details page ("+ Add person"). One row per person,
    strictly scoped to the owning user by TravelerDocumentViewSet. Additive
    model — no existing model or API contract is touched.
    """

    class RelationTag(models.TextChoices):
        SELF = "self", "Myself"
        RELATIVE = "relative", "Relative / companion"

    class IdType(models.TextChoices):
        PASSPORT = "passport", "Passport"
        NATIONAL_ID = "national_id", "National ID"
        DRIVING_LICENSE = "driving_license", "Driving License"
        CITIZENSHIP = "citizenship", "Citizenship Certificate"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="traveler_documents"
    )
    full_name = models.CharField(max_length=200)
    relation_tag = models.CharField(max_length=10, choices=RelationTag.choices, default=RelationTag.SELF)
    relation = models.CharField(max_length=100, blank=True, help_text="e.g. Spouse, Child, Friend")
    phone = models.CharField(max_length=32, blank=True)
    id_type = models.CharField(max_length=20, choices=IdType.choices, default=IdType.PASSPORT)
    id_number = models.CharField(max_length=100, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True, help_text="Allergies, medical info, etc.")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Traveler document"

    def __str__(self):
        return f"{self.full_name} ({self.get_relation_tag_display()})"


class GuideProfile(TimeStampedModel):
    """Reusable professional tourism profile for guides (workforce spec §2/§10).

    A business record lives in MarketplacePartner(kind=guide); this is the
    person-side professional profile with skills, verification and portfolio.
    """

    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending Verification"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_profile")
    headline = models.CharField(max_length=160, blank=True, help_text="One-line professional headline")
    bio = models.TextField(blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    languages = models.JSONField(default=list, blank=True, help_text='["Nepali","English","Japanese"]')
    specializations = models.JSONField(default=list, blank=True, help_text="trekking, cultural, wildlife, city, adventure…")
    certifications = models.JSONField(default=list, blank=True, help_text='[{"name":"…","issuer":"…","year":2024}]')
    license_number = models.CharField(max_length=120, blank=True, help_text="Government guide license where applicable")
    regions = models.JSONField(default=list, blank=True, help_text="Districts/regions covered")
    base_city = models.CharField(max_length=120, blank=True)
    daily_rate_npr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability = models.JSONField(default=dict, blank=True, help_text='{"mon":true,…} or {"from":"2026-10-01","to":"2026-11-15"}')
    portfolio_urls = models.JSONField(default=list, blank=True)
    services = models.JSONField(default=list, blank=True, help_text="Offered services with optional pricing")
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.choices,
                                           default=VerificationStatus.UNVERIFIED, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="guides_verified")
    verification_note = models.TextField(blank=True)
    is_public = models.BooleanField(default=True, help_text="Show in the public guide directory when verified")

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Guide profile: {self.user.email} ({self.verification_status})"


class GuideApplication(TimeStampedModel):
    """Apply-to-become-a-guide workflow (workforce spec §3).

    APPLIED → UNDER_REVIEW → DOCUMENT_VERIFICATION → APPROVED / REJECTED,
    with a NEEDS_INFO side-state for requesting additional information.
    """

    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        UNDER_REVIEW = "under_review", "Under Review"
        DOCUMENT_VERIFICATION = "document_verification", "Document Verification"
        NEEDS_INFO = "needs_info", "Additional Info Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_applications")
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=40, blank=True)
    base_city = models.CharField(max_length=120, blank=True)
    experience_summary = models.TextField(help_text="Guiding/tourism experience")
    languages = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    destinations_covered = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    license_info = models.CharField(max_length=240, blank=True, help_text="Government/license information")
    document_urls = models.JSONField(default=list, blank=True, help_text="Citizenship, license, training certificates…")
    references = models.JSONField(default=list, blank=True)
    expected_daily_rate_npr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.APPLIED, db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="guide_applications_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True, help_text="Latest review note / requested information")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self):
        return f"Guide application {self.full_name} ({self.status})"


class TourismJob(TimeStampedModel):
    """Tourism work/gig listing (workforce spec §9): guides, assistants,
    photographers, translators, hosts, event staff, data contributors…"""

    class RoleType(models.TextChoices):
        GUIDE = "guide", "Tour Guide"
        TREK_ASSISTANT = "trek_assistant", "Trek Assistant"
        PHOTOGRAPHER = "photographer", "Photographer"
        CONTENT_CREATOR = "content_creator", "Content Creator"
        TRANSLATOR = "translator", "Translator"
        CUSTOMER_SUPPORT = "customer_support", "Customer Support"
        HOTEL_STAFF = "hotel_staff", "Hotel Staff"
        TRAVEL_COORDINATOR = "travel_coordinator", "Travel Coordinator"
        EXPERIENCE_HOST = "experience_host", "Local Experience Host"
        EVENT_STAFF = "event_staff", "Event Staff"
        DATA_CONTRIBUTOR = "data_contributor", "Data / Content Contributor"
        OTHER = "other", "Other"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full time"
        PART_TIME = "part_time", "Part time"
        SEASONAL = "seasonal", "Seasonal"
        CONTRACT = "contract", "Contract / gig"
        VOLUNTEER = "volunteer", "Volunteer"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PAUSED = "paused", "Paused"
        FILLED = "filled", "Filled"
        CLOSED = "closed", "Closed"

    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="tourism_jobs_posted")
    title = models.CharField(max_length=200)
    role_type = models.CharField(max_length=24, choices=RoleType.choices, default=RoleType.OTHER, db_index=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    city = models.CharField(max_length=120, blank=True)
    employment_type = models.CharField(max_length=16, choices=EmploymentType.choices, default=EmploymentType.CONTRACT)
    compensation = models.CharField(max_length=160, blank=True, help_text="e.g. NPR 2,500/day or stipend")
    start_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "role_type"])]

    def __str__(self):
        return f"{self.title} ({self.status})"


class TourismJobApplication(TimeStampedModel):
    """Application to a tourism job with a shortlist/hire review flow."""

    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SHORTLISTED = "shortlisted", "Shortlisted"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"

    job = models.ForeignKey(TourismJob, on_delete=models.CASCADE, related_name="applications")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_applications")
    cover_letter = models.TextField()
    experience_summary = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    cv_url = models.URLField(max_length=600, blank=True)
    portfolio_url = models.URLField(max_length=600, blank=True)
    availability = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.APPLIED, db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="job_applications_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("job", "user")

    def __str__(self):
        return f"{self.user.email} → {self.job.title} ({self.status})"


class GuideBookingRequest(TimeStampedModel):
    """Tourist → guide booking request (workforce spec §12).

    Lifecycle: REQUESTED → ACCEPTED/DECLINED → COMPLETED (or CANCELLED).
    Only VERIFIED + public guide profiles can be booked; a review is allowed
    once per completed booking (reputation source, spec §13)."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    tourist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_booking_requests")
    guide_profile = models.ForeignKey("GuideProfile", on_delete=models.CASCADE, related_name="booking_requests")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    group_size = models.PositiveIntegerField(default=1)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tourist.email} → guide {self.guide_profile_id} ({self.status})"


class GuideReview(TimeStampedModel):
    """One review per completed booking (workforce spec §13)."""

    booking = models.OneToOneField(GuideBookingRequest, on_delete=models.CASCADE, related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_reviews")
    guide_profile = models.ForeignKey("GuideProfile", on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}★ for guide {self.guide_profile_id} by {self.user.email}"



# ---------------------------------------------------------------------------
# Administrative geography (task-79 §5): Province -> District as first-class
# records so every district (all 77) has a profile the API can serve. Tourism
# facts are NOT stored here — they come from real Destination/Hospital rows;
# when a district has no verified tourism data the API must say so explicitly
# ("Information unavailable") instead of inventing content.
# ---------------------------------------------------------------------------

class Province(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    capital = models.CharField(max_length=150, blank=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class District(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    slug = models.SlugField(max_length=140, unique=True)
    province = models.ForeignKey(
        Province, on_delete=models.PROTECT, related_name="districts"
    )
    region_type = models.CharField(
        max_length=150, blank=True,
        help_text="Geographic character note from the seed dataset (e.g. 'Hill/Libang (Rolpa Bazar)').",
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    elevation_m = models.IntegerField(null=True, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Curated/verified text. Left blank until verified — the API renders 'Information unavailable', never fabricated copy.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.province.name})"


class TrekkingRoute(models.Model):
    """Verified trekking route. Distinct from road routing: trekking legs are
    trails, not drivable roads, and are never served by the road navigation
    engine. No routes exist until an authoritative source is imported
    (TREKKING DATA DEPENDENCY = EXTERNAL AUTHORITATIVE SOURCE REQUIRED).

    Trust contract: rows are created only by the import/verification pipeline
    (dataset + audit.SourceTier), default unverified, admin promotes. AI or
    user suggestions may never set verification_state to 'verified'."""

    class VerificationState(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified import"
        PENDING = "pending", "Pending admin review"
        VERIFIED = "verified", "Verified against authoritative source"
        REJECTED = "rejected", "Rejected / stale"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MODERATE = "moderate", "Moderate"
        STRENUOUS = "strenuous", "Strenuous"
        EXPEDITION = "expedition", "Expedition grade"

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    region = models.CharField(max_length=120, blank=True,
                              help_text="e.g. Annapurna, Everest, Langtang, Kanchenjunga, Far West.")
    district = models.CharField(max_length=120, blank=True)
    start_point = models.CharField(max_length=180, blank=True)
    end_point = models.CharField(max_length=180, blank=True)
    total_distance_km = models.FloatField(null=True, blank=True)
    total_duration_days = models.IntegerField(null=True, blank=True)
    max_elevation_m = models.IntegerField(null=True, blank=True)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, blank=True)
    best_season = models.CharField(max_length=120, blank=True,
                                   help_text="e.g. 'Mar-May, Sep-Nov'. Blank until verified.")
    permits = models.JSONField(default=list, blank=True,
                               help_text="List of {name, issuer, cost_note}. Empty until verified.")
    accommodation = models.TextField(blank=True)
    safety_notes = models.TextField(blank=True)
    description = models.TextField(
        blank=True,
        help_text="Verified text only. Blank renders 'Information unavailable', never fabricated copy.")
    # Provenance / trust
    source_name = models.CharField(max_length=180, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    source_imported_at = models.DateTimeField(null=True, blank=True)
    verification_state = models.CharField(
        max_length=20, choices=VerificationState.choices,
        default=VerificationState.UNVERIFIED)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.verification_state}]"


class TrekkingStage(models.Model):
    """One leg/day of a TrekkingRoute, ordered, with waypoint coordinates."""
    route = models.ForeignKey(TrekkingRoute, on_delete=models.CASCADE, related_name="stages")
    day_number = models.PositiveIntegerField()
    name = models.CharField(max_length=180, blank=True,
                            help_text="e.g. 'Jomsom to Kalopani'. Blank until verified.")
    from_place = models.CharField(max_length=180, blank=True)
    to_place = models.CharField(max_length=180, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    elevation_gain_m = models.IntegerField(null=True, blank=True)
    elevation_loss_m = models.IntegerField(null=True, blank=True)
    duration_hours = models.FloatField(null=True, blank=True)
    verification_state = models.CharField(
        max_length=20, choices=TrekkingRoute.VerificationState.choices,
        default=TrekkingRoute.VerificationState.UNVERIFIED)

    class Meta:
        ordering = ["route", "day_number"]
        constraints = [
            models.UniqueConstraint(fields=["route", "day_number"], name="uniq_trek_stage_day"),
        ]

    def __str__(self):
        return f"{self.route_id} day {self.day_number}: {self.name or self.to_place or '?'}"


class ConfigPlace(TimeStampedModel):
    """DB-backed home for former hardcoded config place dictionaries.

    V6 §2: MUNICIPALITY_COORDINATES / NEPAL_LANDMARKS previously lived as
    Python dicts inside search code. These rows are canonical database
    records (admin-editable, provenance-tracked) that the search/nearby
    layer now serves instead. Seeded idempotently from the config via
    `manage.py seed_config_places`; coordinates are migrated verbatim from
    the config (provenance recorded), never invented.
    """

    KIND_CHOICES = [
        ("municipality_hub", "Municipality / administrative hub"),
        ("landmark", "Nepal landmark"),
    ]

    config_key = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=30, choices=KIND_CHOICES)
    name = models.CharField(max_length=180)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    district = models.CharField(max_length=80, blank=True)
    province = models.CharField(max_length=60, blank=True)
    city = models.CharField(max_length=120, blank=True)
    category_name = models.CharField(max_length=120, blank=True)
    provenance = models.CharField(
        max_length=300, blank=True,
        help_text="Where these coordinates originally came from (config file + migration date).")
    linked_destination = models.ForeignKey(
        "Destination", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="config_place_aliases",
        help_text="Existing canonical destination this config entry duplicates, if any.")

    class Meta:
        ordering = ["kind", "name"]

    def __str__(self):
        return f"{self.kind}:{self.config_key}"


class PlaceImage(TimeStampedModel):
    """Admin-managed gallery images for any place type (generic).

    Complements DestinationImage (destinations) by covering hotels,
    hospitals, police stations, essential services, trekking routes and
    other place records with one canonical gallery model. Uploaded or
    linked by admins only; missing images stay missing — nothing here is
    ever auto-generated or fabricated.
    """

    SOURCE_CHOICES = [
        ("admin_upload", "Admin upload"),
        ("admin_link", "Admin-provided external URL"),
    ]

    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    place = GenericForeignKey("content_type", "object_id")

    image = models.ImageField(upload_to="places/gallery/", blank=True, null=True)
    external_url = models.URLField(blank=True, help_text="Used instead of `image` for externally-hosted photos.")
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    ordering = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False, help_text="Primary/cover image for the place.")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="admin_upload")
    source_url = models.URLField(max_length=500, blank=True, help_text="Provenance page for externally-hosted images.")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="place_images_uploaded")

    class Meta:
        ordering = ["-is_primary", "ordering", "id"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.image and not self.external_url:
            raise ValidationError("Provide an uploaded image file or an external URL — never both empty, never fabricated.")

    @property
    def resolved_url(self):
        if self.image:
            from .utils import resolve_image_url
            return resolve_image_url(self.image)
        return self.external_url or ""

    def __str__(self):
        return f"PlaceImage({self.content_type.model}:{self.object_id}) {self.caption or self.pk}"


def _cleanup_place_images(sender, instance, **kwargs):
    """Delete gallery rows when their place is deleted (generic FKs do not
    cascade on their own — this prevents orphan image references)."""
    from django.contrib.contenttypes.models import ContentType
    try:
        ct = ContentType.objects.get_for_model(sender)
    except Exception:
        return
    PlaceImage.objects.filter(content_type=ct, object_id=instance.pk).delete()


for _sender in (OSMEssentialService, Hotel, Hospital, PoliceStation, Destination):
    models.signals.post_delete.connect(_cleanup_place_images, sender=_sender,
                                       dispatch_uid=f"placeimage_cleanup_{_sender.__name__}")


class AdminFieldOverride(TimeStampedModel):
    """Provenance: an admin-corrected value that imports must never clobber.

    Recorded whenever an admin edits a record through the CMS (destination
    editor or data explorer). The OSM/import pipeline checks these before
    writing: a differing incoming value becomes an ImportConflict for admin
    review instead of a silent overwrite (spec §8).
    """

    model_label = models.CharField(max_length=80, db_index=True)   # e.g. "tourist.hospital"
    object_id = models.PositiveIntegerField(db_index=True)
    field = models.CharField(max_length=80)
    value = models.TextField(blank=True)
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="field_overrides"
    )
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("model_label", "object_id", "field")

    def __str__(self):
        return f"{self.model_label}#{self.object_id}.{self.field}"


class ImportConflict(TimeStampedModel):
    """A pending 'suggested update': import value differs from the admin's.

    Only after an admin resolves the conflict (keep current / accept new /
    edit) may the database value change (spec §9).
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        KEPT = "kept", "Kept Current"
        ACCEPTED = "accepted", "Accepted New"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="import_conflicts")
    field = models.CharField(max_length=80)
    current_value = models.TextField(blank=True)
    proposed_value = models.TextField(blank=True)
    source = models.CharField(max_length=80, default="osm_csv")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="resolved_import_conflicts"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["destination", "field", "status"])]

    def __str__(self):
        return f"{self.destination_id}.{self.field}: {self.current_value!r} -> {self.proposed_value!r} [{self.status}]"


class DuplicateDecision(TimeStampedModel):
    """Admin dismissal of a duplicate-candidate pair (§10 'Not Duplicate').

    Stored with the pair ids in ascending order so a pair can only be
    dismissed once; the detection service excludes dismissed pairs.
    """

    id_a = models.PositiveIntegerField()
    id_b = models.PositiveIntegerField()
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="duplicate_decisions"
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("id_a", "id_b")

    def save(self, *args, **kwargs):
        if self.id_a > self.id_b:
            self.id_a, self.id_b = self.id_b, self.id_a
        super().save(*args, **kwargs)

    def __str__(self):
        return f"not-duplicate: #{self.id_a} / #{self.id_b}"
