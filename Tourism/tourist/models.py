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
        FIELD_VERIFIER = "field_verifier", "Field Verifier"

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

    best_time_to_visit = models.CharField(
        max_length=200, blank=True, null=True,
        help_text="e.g. 'October to December, and March to April' -- can be AI-generated if left blank."
    )
    content_ai_generated = models.BooleanField(
        default=False, help_text="True if description/best_time_to_visit were filled by AI generation rather than typed by a human."
    )


    district = models.CharField(
        max_length=100,
        blank=True,
        null=True
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

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="destinations/gallery/", blank=True, null=True)
    external_url = models.URLField(
        blank=True, help_text="Used instead of `image` for externally-hosted photos (Unsplash/Wikimedia/etc.)"
    )
    caption = models.CharField(max_length=200, blank=True)
    is_cover = models.BooleanField(default=False)

    source = models.CharField(max_length=20, choices=Source.choices, default=Source.ADMIN)
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
        ordering = ["-is_cover", "-is_promoted", "-view_count", "-created_at"]

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


class Itinerary(TimeStampedModel):
    """
    A planned multi-day trip -- persisted, unlike ml_service's
    itinerary_service.py which only ever produced a one-off response
    and never saved anything. This is the actual "plan through
    execution" record: created while planning, progresses through
    real-world travel as ItineraryStops get marked visited.
    """
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        CONFIRMED = "confirmed", "Confirmed"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="itineraries")
    title = models.CharField(max_length=200, blank=True, help_text="e.g. 'Annapurna Circuit, June 2026'")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    start_date = models.DateField(null=True, blank=True)
    num_days = models.PositiveSmallIntegerField(default=1)
    # The category/categories used to filter destination choices while
    # building this itinerary, e.g. ["trekking", "cultural"] -- kept for
    # reference/re-filtering, not enforced on the stops themselves (a
    # user can still add a destination outside the original filter).
    category_filter = models.ManyToManyField(Category, blank=True, related_name="itineraries")
    total_distance_km = models.FloatField(null=True, blank=True, help_text="Filled in when the plan is generated via the route engine.")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title or 'Itinerary'} ({self.user}) -- {self.status}"

    @property
    def progress(self):
        """e.g. '3/8 stops visited' -- the actual plan-to-execution tracking."""
        stops = ItineraryStop.objects.filter(day__itinerary=self)
        total = stops.count()
        visited = stops.filter(is_visited=True).count()
        return {"total": total, "visited": visited}


class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveSmallIntegerField()
    date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["day_number"]
        unique_together = ["itinerary", "day_number"]


class ItineraryStop(models.Model):
    day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name="stops")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="itinerary_stops")
    order = models.PositiveSmallIntegerField(default=0, help_text="Order within the day.")
    distance_from_previous_km = models.FloatField(
        null=True, blank=True,
        help_text="Route distance from the previous stop (same day) or previous day's last stop -- filled in via the route engine when the plan is generated."
    )
    notes = models.TextField(blank=True)
    # The actual plan-to-execution tracking at the per-stop level.
    is_visited = models.BooleanField(default=False)
    visited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.destination.name} (Day {self.day.day_number})"


class VisitHistory(models.Model):
    """Tracks destinations a user has viewed/visited."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="history")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="visit_history")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        verbose_name_plural = "Visit history"


class FieldVerificationTask(TimeStampedModel):
    """
    An assignment: "go check this place is real/accurate". Created by
    an admin/moderator, assigned to a FIELD_VERIFIER-role user.
    """
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Report Submitted"
        REVIEWED = "reviewed", "Reviewed"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="verification_tasks")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verification_tasks"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks_assigned"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    due_date = models.DateField(null=True, blank=True)
    instructions = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verify {self.destination.name} -- {self.assigned_to} ({self.status})"


class FieldVerificationReport(TimeStampedModel):
    """
    What the field employee actually submits after visiting. Structured
    fields here double as future ML risk-model training data (the
    landslide/avalanche/flood/sickness/accident/transport-ease/local-
    helpfulness observations) -- not auto-fed into the model yet (that's
    a separate, deliberate training-pipeline step, not something that
    should happen silently on every report submission), but the real
    structured data collection point that was missing before.
    """
    class HelpfulnessLevel(models.TextChoices):
        VERY_HELPFUL = "very_helpful", "Very Helpful"
        SOMEWHAT_HELPFUL = "somewhat_helpful", "Somewhat Helpful"
        NEUTRAL = "neutral", "Neutral"
        UNHELPFUL = "unhelpful", "Unhelpful"

    class TransportEase(models.TextChoices):
        EASY = "easy", "Easy to reach"
        MODERATE = "moderate", "Moderately difficult"
        DIFFICULT = "difficult", "Difficult"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    task = models.OneToOneField(FieldVerificationTask, on_delete=models.CASCADE, related_name="report")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="verification_reports")
    visit_date = models.DateField()

    # Accuracy of the existing listing
    is_place_accurate = models.BooleanField(default=True)
    accuracy_notes = models.TextField(blank=True, help_text="What's wrong, if is_place_accurate is False.")

    # Real-world risk observations -- the structured data the earlier ML
    # data-collection request was asking for.
    witnessed_sickness = models.BooleanField(default=False)
    witnessed_accident = models.BooleanField(default=False)
    witnessed_misleading_activity = models.BooleanField(default=False, help_text="Scams, overcharging, false guiding, etc.")
    hazards_observed = models.JSONField(
        default=list, blank=True,
        help_text='e.g. ["avalanche_risk", "flood_risk", "landslide_risk"] -- any real-world hazard signs seen on this visit.'
    )
    transport_ease = models.CharField(max_length=10, choices=TransportEase.choices, blank=True)
    local_helpfulness = models.CharField(max_length=20, choices=HelpfulnessLevel.choices, blank=True)
    local_behavior_notes = models.TextField(blank=True, help_text="General notes on how locals greeted/treated visitors.")

    general_notes = models.TextField(blank=True)

    review_status = models.CharField(max_length=10, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports_reviewed"
    )
    review_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report: {self.task.destination.name} by {self.submitted_by} ({self.review_status})"


class FieldVerificationPhoto(models.Model):
    """Photos submitted as evidence with a report -- separate from DestinationImage since these need review before being promoted to a real gallery photo."""
    report = models.ForeignKey(FieldVerificationReport, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="field_verification/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class TripFeedback(TimeStampedModel):
    """
    Real-world outcome feedback from a completed (or in-progress)
    Itinerary -- what it actually cost, how the routes/hotels/
    restaurants actually were. This is the structured data source for
    "next time, remember this" personalization/ML training that a much
    earlier request in this project asked for: real trip outcomes
    feeding future budget estimates, recommendations, and route
    planning -- not auto-applied to those models on submission (that's
    a deliberate separate training/aggregation step, same reasoning as
    FieldVerificationReport not auto-feeding risk_engine.py), but this
    is the real collection point that didn't exist before.
    """
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="feedback")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trip_feedback")

    # Real costs actually incurred -- compared against the original
    # budget estimate for that itinerary to measure estimate accuracy.
    num_people = models.PositiveSmallIntegerField(default=1)
    actual_total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_travel_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_entry_fees_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_food_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    extra_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    extra_cost_note = models.CharField(max_length=200, blank=True, help_text="What the extra cost was for, if any.")

    # Route/hotel/restaurant feedback
    route_rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5, how good the suggested route actually was.")
    route_notes = models.TextField(blank=True)
    hotel_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    hotel_notes = models.TextField(blank=True)
    restaurant_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    restaurant_notes = models.TextField(blank=True)

    general_suggestion = models.TextField(blank=True, help_text="Open suggestion box -- anything else worth telling future travelers/the recommendation engine.")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback on {self.itinerary} by {self.submitted_by}"


class TripFeedbackMedia(models.Model):
    """
    Proof/description media attached to feedback -- images AND video,
    both supported (video was explicitly asked for and didn't exist
    anywhere in the project before this).
    """
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    feedback = models.ForeignKey(TripFeedback, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to="trip_feedback/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Restaurant(TimeStampedModel):
    """
    Dining options near a destination -- mirrors Hotel's shape exactly
    (same source-tracking, same image handling), since it didn't exist
    at all before and Hotel is the proven-correct pattern to copy.
    """
    class Source(models.TextChoices):
        DATASET = "dataset", "Imported Dataset"
        GOOGLE_PLACES = "google_places", "Google Places"
        FOURSQUARE = "foursquare", "Foursquare"
        MANUAL = "manual", "Manually Added"

    class PriceRange(models.TextChoices):
        BUDGET = "budget", "$ Budget"
        MID = "mid", "$$ Mid-range"
        UPSCALE = "upscale", "$$$ Upscale"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="restaurants")
    name = models.CharField(max_length=200)
    cuisine_type = models.CharField(max_length=100, blank=True, help_text="e.g. 'Nepali', 'Newari', 'Continental', 'Multi-cuisine'")
    price_range = models.CharField(max_length=10, choices=PriceRange.choices, default=PriceRange.MID)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)
    booking_url = models.URLField(blank=True, help_text="Link to book/order externally, if available.")
    cover_image = models.ImageField(upload_to="restaurants/covers/", blank=True, null=True)
    external_image_url = models.URLField(blank=True)
    dietary_options = models.JSONField(
        default=list, blank=True,
        help_text='e.g. ["vegetarian", "vegan", "halal", "gluten_free"]'
    )
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.DATASET)

    class Meta:
        ordering = ["-rating"]

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


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
    cover_image = models.ImageField(upload_to="hospitals/", blank=True, null=True)
    external_image_url = models.URLField(blank=True)


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
    cover_image = models.ImageField(upload_to="police_stations/", blank=True, null=True)
    external_image_url = models.URLField(blank=True)


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

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
# Notification, DeviceToken moved to notifications/models.py
# TrustedContact, SharedTrip, LocationPing, SOSAlert moved to safety/models.py


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