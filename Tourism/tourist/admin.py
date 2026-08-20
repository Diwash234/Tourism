from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User, Language, Category, Destination, DestinationTranslation,
    DestinationImage, DestinationVideo, Review, Rating, Favorite,
    VisitHistory, Budget, Alert, EmergencyContact, Notification,
    DeviceToken, EmailVerificationToken, PasswordResetToken, MLInsight, Hotel,
    OSMEssentialService, OSMTourismPlace, FamilyLink, RiskIncident, CurrentHazard,
    InfrastructureSubmission, DestinationFeatureProfile, FeedbackEvidence, MLTrainingRun,
    RecommendationEvent, RiskNewsReport, RiskObservation, UserFeedback, StaffCapabilityProfile,
    SiteSetting, ManagedPage, ContentSection, ManagedNavigationItem, CMSRevision, FeedbackMessage,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "full_name", "role", "is_verified", "is_active", "is_staff", "date_joined"]
    list_filter = ["role", "is_verified", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["date_joined", "last_login"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "bio", "profile_picture")}),
        ("Location", {"fields": ("latitude", "longitude", "country", "city", "location_source")}),
        ("Preferences", {"fields": ("preferred_language", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_verified", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    filter_horizontal = ["groups", "user_permissions"]


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "destination_count"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

    def destination_count(self, obj):
        return obj.destinations.count()
    destination_count.short_description = "Destinations"


# ---------------------------------------------------------------------------
# Destination image moderation inline
# ---------------------------------------------------------------------------
class DestinationImageInline(admin.TabularInline):
    model = DestinationImage
    extra = 0
    fields = [
        "thumbnail", "image", "external_url", "caption",
        "is_cover", "source", "verification_status",
        "is_verified", "authenticity_score",
        "uploaded_by", "view_count",
    ]
    readonly_fields = ["thumbnail", "view_count"]
    ordering = ["-is_cover", "-created_at"]
    max_num = 20

    def thumbnail(self, obj):
        url = None
        if obj.external_url:
            url = obj.external_url
        elif obj.image:
            try:
                url = obj.image.url
            except Exception:
                url = None
        if url:
            return format_html(
                '<img src="{}" style="height:60px;width:60px;object-fit:cover;border-radius:6px;" />',
                url,
            )
        return "—"
    thumbnail.short_description = "Preview"


class DestinationVideoInline(admin.TabularInline):
    model = DestinationVideo
    extra = 0


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = [
        "name", "cover_thumb", "category", "city", "district",
        "status", "image_count", "average_rating", "views_count", "is_active",
    ]
    list_filter = ["category", "country", "province", "district", "status", "is_active"]
    search_fields = ["name", "slug", "city", "district", "province", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DestinationImageInline, DestinationVideoInline]
    readonly_fields = [
        "average_rating", "ratings_count", "views_count",
        "created_at", "updated_at", "cover_image_preview", "cover_image_url_preview",
    ]
    list_per_page = 50
    actions = [
        "approve_selected",
        "reject_selected",
        "reassign_covers_action",
    ]

    def cover_thumb(self, obj):
        """Tiny cover preview in the list view so admins can spot wrong-category images at a glance."""
        url = None
        cover = obj.gallery.filter(is_cover=True).first()
        if cover and cover.external_url:
            url = cover.external_url
        elif cover and cover.image:
            try:
                url = cover.image.url
            except Exception:
                url = None
        elif obj.cover_image:
            try:
                url = obj.cover_image.url
            except Exception:
                url = None
        if url:
            return format_html(
                '<img src="{}" style="height:44px;width:64px;object-fit:cover;border-radius:4px;" />',
                url,
            )
        return "—"
    cover_thumb.short_description = "Cover"

    def image_count(self, obj):
        return obj.gallery.count()
    image_count.short_description = "#Images"

    def cover_image_preview(self, obj):
        """Big cover preview on the edit page."""
        url = None
        cover = obj.gallery.filter(is_cover=True).first()
        if cover and cover.external_url:
            url = cover.external_url
        elif cover and cover.image:
            try:
                url = cover.image.url
            except Exception:
                url = None
        elif obj.cover_image:
            try:
                url = obj.cover_image.url
            except Exception:
                url = None
        if url:
            return format_html(
                '<img src="{}" style="max-height:220px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.1);" />'
                '<p style="color:#666;font-size:12px;">Current cover (upload replacement in inline below).</p>',
                url,
            )
        return "No cover image yet."
    cover_image_preview.short_description = "Current cover image"

    def cover_image_url_preview(self, obj):
        cover = obj.gallery.filter(is_cover=True).first()
        if cover and cover.external_url:
            return cover.external_url
        return ""
    cover_image_url_preview.short_description = "Cover URL"

    @admin.action(description="Approve selected pending submissions")
    def approve_selected(self, request, queryset):
        updated = queryset.update(status=Destination.SubmissionStatus.APPROVED, is_active=True)
        self.message_user(request, f"{updated} destination(s) approved.")

    @admin.action(description="Reject selected pending submissions")
    def reject_selected(self, request, queryset):
        updated = queryset.update(status=Destination.SubmissionStatus.REJECTED, is_active=False)
        self.message_user(request, f"{updated} destination(s) rejected.")

    @admin.action(description="Reassign deterministic cover + 6 gallery photos (from catalog)")
    def reassign_covers_action(self, request, queryset):
        """Run the photo_catalog resolver on just the selected destinations."""
        from . import photo_catalog
        processed = 0
        for dest in queryset:
            # Clear any existing auto-assigned covers first
            dest.gallery.filter(
                source__in=[
                    DestinationImage.Source.UNSPLASH,
                    DestinationImage.Source.REFERENCE,
                ],
                is_cover=True,
            ).update(is_cover=False)

            try:
                cover = photo_catalog.resolve_cover_photo(dest)
            except Exception as exc:  # noqa: BLE001
                self.message_user(
                    request, f"Cover resolution failed for {dest.name}: {exc}",
                    level="error",
                )
                continue
            gallery = photo_catalog.resolve_gallery_photos(dest, target=6)

            seen_urls = set(
                dest.gallery.values_list("external_url", flat=True),
            )
            # Add cover
            if cover.get("url") and cover["url"] not in seen_urls:
                _make_image(dest, cover, is_cover=True)
            elif cover.get("url"):
                dest.gallery.filter(external_url=cover["url"]).update(is_cover=True)
            seen_urls.add(cover.get("url"))

            for photo in gallery:
                u = photo.get("url")
                if u and u not in seen_urls:
                    _make_image(dest, photo, is_cover=False)
                    seen_urls.add(u)
            processed += 1
        self.message_user(
            request,
            f"Re-assigned photos for {processed} destination(s) using curated catalog.",
        )


def _make_image(dest, photo, *, is_cover):
    """Helper that creates a DestinationImage row from a photo_catalog dict."""
    url = photo.get("url", "")
    if not url:
        return
    if url.startswith("/images/"):
        source = DestinationImage.Source.REFERENCE
        authenticity = 0.95
    elif "images.unsplash.com" in url:
        source = DestinationImage.Source.UNSPLASH
        authenticity = 0.65
    else:
        source = DestinationImage.Source.UNSPLASH
        authenticity = 0.5
    DestinationImage.objects.get_or_create(
        destination=dest,
        external_url=url,
        defaults=dict(
            thumbnail_url=photo.get("thumb", url),
            caption=(photo.get("caption", "") or "")[:200],
            is_cover=is_cover,
            source=source,
            source_url=photo.get("source_url", "")[:500],
            photographer=(photo.get("author", "") or "")[:150],
            license_type=(photo.get("license", "") or "")[:100],
            copyright_status="verified_reusable",
            image_category="cover" if is_cover else "gallery",
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
            authenticity_score=authenticity,
            quality_score=0.8,
            attribution=(photo.get("author", "") or "")[:120],
        ),
    )


@admin.register(DestinationImage)
class DestinationImageAdmin(admin.ModelAdmin):
    list_display = ["thumbnail", "destination", "is_cover", "source", "verification_status", "is_verified", "view_count", "created_at"]
    list_filter = ["is_cover", "source", "verification_status", "is_verified"]
    search_fields = ["destination__name", "caption", "external_url"]
    list_per_page = 100
    actions = ["approve_selected_images", "reject_selected_images", "mark_verified"]
    readonly_fields = ["thumbnail_large", "view_count", "phash", "quality_score", "authenticity_score", "overall_score"]

    def thumbnail(self, obj):
        url = None
        if obj.external_url:
            url = obj.external_url
        elif obj.image:
            try:
                url = obj.image.url
            except Exception:
                url = None
        if url:
            return format_html(
                '<img src="{}" style="height:44px;width:64px;object-fit:cover;border-radius:4px;" />', url,
            )
        return "—"
    thumbnail.short_description = "Thumb"

    def thumbnail_large(self, obj):
        url = None
        if obj.external_url:
            url = obj.external_url
        elif obj.image:
            try:
                url = obj.image.url
            except Exception:
                url = None
        if url:
            return format_html('<img src="{}" style="max-height:300px;border-radius:8px;" />', url)
        return "—"
    thumbnail_large.short_description = "Full preview"

    @admin.action(description="Approve selected images")
    def approve_selected_images(self, request, qs):
        n = qs.update(verification_status=DestinationImage.ImageStatus.APPROVED, is_verified=True)
        self.message_user(request, f"{n} images approved.")

    @admin.action(description="Reject selected images")
    def reject_selected_images(self, request, qs):
        n = qs.update(verification_status=DestinationImage.ImageStatus.REJECTED, is_verified=False)
        self.message_user(request, f"{n} images rejected.")

    @admin.action(description="Mark as verified")
    def mark_verified(self, request, qs):
        n = qs.update(is_verified=True, verification_status=DestinationImage.ImageStatus.APPROVED)
        self.message_user(request, f"{n} images marked verified.")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ["name", "destination", "image_preview", "booking_status", "price_per_night", "currency", "rating", "source"]
    list_filter = ["booking_status", "source", "currency"]
    search_fields = ["name", "destination__name", "address"]
    readonly_fields = ["image_preview_large"]
    fields = [
        "destination", "name", "cover_image", "external_image_url", "image_preview_large",
        "price_per_night", "currency", "rating", "booking_status", "booking_url",
        "facilities", "address", "latitude", "longitude", "source", "phone",
    ]

    @admin.display(description="Image")
    def image_preview(self, obj):
        url = None
        if obj.cover_image:
            try:
                url = obj.cover_image.url
            except Exception:
                url = None
        if not url and obj.external_image_url:
            url = obj.external_image_url
        if url:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', url)
        return "—"

    @admin.display(description="Current image")
    def image_preview_large(self, obj):
        url = None
        if obj.cover_image:
            try:
                url = obj.cover_image.url
            except Exception:
                url = None
        if not url and obj.external_image_url:
            url = obj.external_image_url
        if url:
            return format_html('<img src="{}" style="max-height:200px;border-radius:8px;" />', url)
        return "No image yet."


@admin.register(DestinationTranslation)
class DestinationTranslationAdmin(admin.ModelAdmin):
    list_display = ["destination", "language", "is_auto_generated", "updated_at"]
    list_filter = ["language", "is_auto_generated"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["destination", "user", "is_flagged", "created_at"]
    list_filter = ["is_flagged"]


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["destination", "user", "value", "created_at"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "destination", "created_at"]


@admin.register(VisitHistory)
class VisitHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "destination", "viewed_at"]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "category", "amount", "currency", "date"]
    list_filter = ["category", "currency"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["title", "alert_type", "severity", "city", "is_active", "created_at"]
    list_filter = ["alert_type", "severity", "is_active"]
    search_fields = ["title", "city", "country"]


@admin.register(RiskIncident)
class RiskIncidentAdmin(admin.ModelAdmin):
    list_display = ["title", "destination", "hazard_type", "severity", "event_date", "source_type", "verified"]
    list_filter = ["hazard_type", "severity", "source_type", "verified"]
    search_fields = ["title", "destination__name", "source_name"]
    autocomplete_fields = ["destination"]


@admin.register(CurrentHazard)
class CurrentHazardAdmin(admin.ModelAdmin):
    list_display = ["title", "destination", "hazard_type", "severity", "source_name", "observed_at", "is_active", "verified"]
    list_filter = ["hazard_type", "severity", "source_type", "is_active", "verified"]
    search_fields = ["title", "destination__name", "source_name", "station_name"]
    autocomplete_fields = ["destination"]


@admin.register(InfrastructureSubmission)
class InfrastructureSubmissionAdmin(admin.ModelAdmin):
    list_display = ["name", "place_type", "district", "province", "status", "submitted_by", "created_at"]
    list_filter = ["place_type", "status", "province", "district"]
    search_fields = ["name", "address", "municipality", "submitted_by__email"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at", "csv_synced_at"]


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_type", "ward_number", "designation", "city", "phone_number", "is_24_hours"]
    list_filter = ["contact_type", "city", "ward_number"]
    search_fields = ["name", "city", "designation"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "channel", "title", "is_read", "is_sent", "created_at"]
    list_filter = ["channel", "is_read", "is_sent"]


admin.site.register(DeviceToken)
admin.site.register(EmailVerificationToken)
admin.site.register(PasswordResetToken)


@admin.register(MLInsight)
class MLInsightAdmin(admin.ModelAdmin):
    list_display = ["destination", "insight_type", "label", "score", "created_at"]
    list_filter = ["insight_type"]


admin.site.site_header = "Nepal Tourism Platform — Administration"
admin.site.site_title = "Nepal Tourism Admin"
admin.site.index_title = "Manage Destinations, Images, Alerts & Users"


@admin.register(OSMEssentialService)
class OSMEssentialServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "phone", "address"]
    list_filter = ["category"]
    search_fields = ["name", "address"]


@admin.register(OSMTourismPlace)
class OSMTourismPlaceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "address"]
    list_filter = ["category"]
    search_fields = ["name", "address"]


@admin.register(FamilyLink)
class FamilyLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "requester", "member", "relationship", "status", "created_at", "accepted_at"]
    list_filter = ["status"]
    search_fields = ["requester__email", "member__email", "requester__first_name", "member__first_name"]
    readonly_fields = ["created_at", "accepted_at"]


@admin.register(DestinationFeatureProfile)
class DestinationFeatureProfileAdmin(admin.ModelAdmin):
    list_display = ["destination", "difficulty", "budget_level", "is_verified", "updated_at"]
    list_filter = ["difficulty", "budget_level", "is_verified"]
    search_fields = ["destination__name"]


@admin.register(RiskObservation)
class RiskObservationAdmin(admin.ModelAdmin):
    list_display = ["destination", "observation_type", "value", "unit", "station_name", "observed_at", "verified"]
    list_filter = ["observation_type", "trend", "verified"]
    search_fields = ["destination__name", "station_name", "source_name"]


@admin.register(RiskNewsReport)
class RiskNewsReportAdmin(admin.ModelAdmin):
    list_display = ["title", "destination", "hazard_type", "source_name", "published_at", "verification_status"]
    list_filter = ["hazard_type", "verification_status", "promoted_to_warning"]
    search_fields = ["title", "destination__name", "affected_area", "source_name"]


@admin.register(MLTrainingRun)
class MLTrainingRunAdmin(admin.ModelAdmin):
    list_display = ["model_type", "version", "status", "dataset_size", "requested_by", "created_at"]
    list_filter = ["model_type", "status"]
    readonly_fields = ["created_at", "updated_at", "started_at", "completed_at"]


@admin.register(RecommendationEvent)
class RecommendationEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "user", "destination", "score", "consented", "created_at"]
    list_filter = ["event_type", "consented"]


@admin.register(FeedbackEvidence)
class FeedbackEvidenceAdmin(admin.ModelAdmin):
    list_display = ["feedback", "media_type", "caption", "is_verified", "created_at"]
    list_filter = ["media_type", "is_verified"]


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ["subject", "user", "email", "category", "status", "created_at"]
    list_filter = ["category", "status", "created_at"]
    search_fields = ["subject", "message", "name", "email", "user__email"]
    readonly_fields = ["created_at", "updated_at", "replied_at"]


@admin.register(StaffCapabilityProfile)
class StaffCapabilityProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "assigned_by", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    autocomplete_fields = ["user", "assigned_by"]

class ContentSectionInline(admin.TabularInline):
    model=ContentSection; extra=0; ordering=['display_order']

@admin.register(ManagedPage)
class ManagedPageAdmin(admin.ModelAdmin):
    list_display=['title','route','is_enabled','status','scheduled_publish_at','published_at','updated_at']; list_filter=['is_enabled','status']; search_fields=['title','route','key']; inlines=[ContentSectionInline]

@admin.register(CMSRevision)
class CMSRevisionAdmin(admin.ModelAdmin):
    list_display=['resource','object_id','revision_number','action','created_by','created_at']
    list_filter=['resource','action']; search_fields=['object_id','created_by__email']; readonly_fields=['resource','object_id','revision_number','snapshot','action','created_by','created_at']
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display=['key','is_public','updated_by','updated_at']; list_filter=['is_public']; search_fields=['key','description']

@admin.register(ManagedNavigationItem)
class ManagedNavigationItemAdmin(admin.ModelAdmin):
    list_display=['label','location','route','parent','display_order','is_active']; list_filter=['location','is_active']; search_fields=['label','route']

@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(admin.ModelAdmin):
    list_display=['feedback','sender','is_internal','created_at']; list_filter=['is_internal']; search_fields=['body','feedback__subject']
