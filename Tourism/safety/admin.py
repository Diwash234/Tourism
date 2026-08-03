# from django.contrib import admin

# from .models import TrustedContact, SharedTrip, LocationPing, SOSAlert


# @admin.register(TrustedContact)
# class TrustedContactAdmin(admin.ModelAdmin):
#     list_display = ["name", "user", "relationship", "email", "phone_number"]
#     search_fields = ["name", "user__email", "email"]


# class LocationPingInline(admin.TabularInline):
#     model = LocationPing
#     extra = 0
#     readonly_fields = ["latitude", "longitude", "recorded_at"]
#     can_delete = False


# @admin.register(SharedTrip)
# class SharedTripAdmin(admin.ModelAdmin):
#     list_display = ["label", "user", "is_active", "started_at", "expires_at"]
#     list_filter = ["is_active"]
#     search_fields = ["label", "user__email"]
#     readonly_fields = ["share_token", "started_at"]
#     inlines = [LocationPingInline]


# @admin.register(SOSAlert)
# class SOSAlertAdmin(admin.ModelAdmin):
#     list_display = ["user", "status", "triggered_at", "resolved_at"]
#     list_filter = ["status"]
#     search_fields = ["user__email", "message"]
#     readonly_fields = ["triggered_at"]