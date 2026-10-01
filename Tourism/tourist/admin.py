"""
Admin configuration for the Tourism models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Destination, Category, DestinationImage, Review, ManagedPage, ContentSection


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_verified", "is_active")
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "district", "province", "status")
    list_filter = ("status", "category", "province", "district")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("created_by", "category")


@admin.register(DestinationImage)
class DestinationImageAdmin(admin.ModelAdmin):
    list_display = ("id", "destination", "is_cover", "verification_status", "is_verified")
    list_filter = ("verification_status", "is_verified", "is_cover")
    search_fields = ("destination__name",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "destination", "moderation_status", "is_flagged", "created_at")
    list_filter = ("moderation_status", "is_flagged", "created_at")
    search_fields = ("user__email", "destination__name", "comment")

class ContentSectionInline(admin.TabularInline):
    """Sections edited here go through the same storage boundary as the API.

    A bare inline skipped every guarantee AdminCMSView enforces: ``body`` was
    stored verbatim (no ``sanitize_cms_html``), ``config`` was not whitelisted,
    and no CMSRevision / AuditLog row was written and the public CMS cache was
    never invalidated. Because PublicConfigView falls back to live section rows
    when ``published_snapshot`` is empty, an admin form save could therefore
    publish unsanitized markup straight to the public site.

    The enforcement lives in ManagedPageAdmin.save_formset because
    ``save_formset`` is a ModelAdmin hook -- InlineModelAdmin does not have one.
    """
    model=ContentSection; extra=0; ordering=['display_order']
@admin.register(ManagedPage)
class ManagedPageAdmin(admin.ModelAdmin):
    list_display=['title','route','is_enabled','status','scheduled_publish_at','published_at','updated_at']; list_filter=['is_enabled','status']; search_fields=['title','route','key']; inlines=[ContentSectionInline]

    def save_formset(self, request, form, formset, change):
        """Apply the API's storage boundary to inline section saves.

        ``save_formset`` runs before ``formset.save()``, so sanitizing the form
        instances here means nothing unsanitized can reach the database through
        the admin, exactly as with the JSON API.
        """
        from .views_admin import AdminCMSView, sanitize_cms_html

        if formset.model is ContentSection:
            changed = False
            for inline_form in formset.forms:
                if not inline_form.has_changed():
                    continue
                section = inline_form.instance
                section.body = sanitize_cms_html(section.body)
                if isinstance(section.config, dict):
                    section.config = AdminCMSView._safe_section_config(section.config)
                changed = True
            if changed:
                AdminCMSView._invalidate_public_caches()
        super().save_formset(request, form, formset, change)
