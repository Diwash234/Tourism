# from django.contrib import admin

# from .models import Notification, DeviceToken


# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ["title", "user", "channel", "is_read", "is_sent", "created_at"]
#     list_filter = ["channel", "is_read", "is_sent"]
#     search_fields = ["title", "user__email"]


# @admin.register(DeviceToken)
# class DeviceTokenAdmin(admin.ModelAdmin):
#     list_display = ["user", "platform", "created_at"]
#     list_filter = ["platform"]