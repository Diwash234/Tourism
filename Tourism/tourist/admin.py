"""
Admin configuration for the Tourism models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Destination, Category, DestinationImage, Review


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_verified", "is_active")
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "ordering")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "district", "province", "is_published", "is_featured")
    list_filter = ("is_published", "is_featured", "category", "province", "district")
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
    list_display = ("id", "user", "destination", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved", "created_at")
    search_fields = ("user__email", "destination__name", "comment")
