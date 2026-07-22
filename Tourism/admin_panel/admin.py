from django.contrib import admin

from .models import HotelAssignment, AdminTask


@admin.register(HotelAssignment)
class HotelAssignmentAdmin(admin.ModelAdmin):
    list_display = ["hotel", "admin", "assigned_by", "assigned_at"]
    list_filter = ["hotel"]
    search_fields = ["hotel__name", "admin__email"]


@admin.register(AdminTask)
class AdminTaskAdmin(admin.ModelAdmin):
    list_display = ["title", "assigned_to", "assigned_by", "status", "priority", "due_date"]
    list_filter = ["status", "priority"]
    search_fields = ["title", "assigned_to__email"]