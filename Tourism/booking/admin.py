from django.contrib import admin

from .models import Booking, HotelReview


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["user", "hotel", "check_in", "check_out", "status", "total_price"]
    list_filter = ["status", "hotel"]
    search_fields = ["user__email", "hotel__name"]


@admin.register(HotelReview)
class HotelReviewAdmin(admin.ModelAdmin):
    list_display = ["hotel", "user", "rating", "moderation_status", "moderated_by", "created_at"]
    list_filter = ["rating", "moderation_status"]
    search_fields = ["hotel__name", "user__email", "comment"]