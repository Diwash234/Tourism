from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User, Language, Category, Destination, DestinationTranslation,
    DestinationImage, DestinationVideo, Review, Rating, Favorite,
    VisitHistory, Budget, Alert, EmergencyContact, Notification,
    DeviceToken, EmailVerificationToken, PasswordResetToken, MLInsight,
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
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class DestinationImageInline(admin.TabularInline):
    model = DestinationImage
    extra = 1


class DestinationVideoInline(admin.TabularInline):
    model = DestinationVideo
    extra = 0


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "city", "status", "is_user_submitted", "average_rating", "views_count", "is_active", "created_at"]
    list_filter = ["category", "country", "status", "is_user_submitted", "is_active"]
    search_fields = ["name", "city", "country", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DestinationImageInline, DestinationVideoInline]
    readonly_fields = ["average_rating", "ratings_count", "views_count", "created_at", "updated_at"]
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected pending submissions")
    def approve_selected(self, request, queryset):
        updated = queryset.update(status=Destination.SubmissionStatus.APPROVED, is_active=True)
        self.message_user(request, f"{updated} destination(s) approved.")

    @admin.action(description="Reject selected pending submissions")
    def reject_selected(self, request, queryset):
        updated = queryset.update(status=Destination.SubmissionStatus.REJECTED, is_active=False)
        self.message_user(request, f"{updated} destination(s) rejected.")


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


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_type", "city", "phone_number", "is_24_hours"]
    list_filter = ["contact_type", "city"]
    search_fields = ["name", "city"]


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

admin.site.site_header = "Local Tourism Information Portal Administration"
admin.site.site_title = "Tourism Portal Admin"
admin.site.index_title = "Manage Destinations, Alerts & Users"