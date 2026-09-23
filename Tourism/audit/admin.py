from django.contrib import admin
from .models import AuditLog, ErrorEvent, HealthSample


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "severity", "category", "action", "user_email",
                    "endpoint", "status_code", "source")
    list_filter = ("severity", "category", "source", "timestamp")
    search_fields = ("action", "message", "endpoint", "user_email", "object_type")
    readonly_fields = (
        "timestamp", "user", "ip_address", "actor_role", "category", "severity",
        "source", "action", "message", "object_type", "object_id",
        "endpoint", "method", "status_code", "extra",
    )
    date_hierarchy = "timestamp"
    list_per_page = 50


@admin.register(ErrorEvent)
class ErrorEventAdmin(admin.ModelAdmin):
    list_display = ("last_seen", "resolved", "severity", "source", "error_type",
                    "endpoint", "occurrences", "status_code")
    list_filter = ("resolved", "severity", "source", "last_seen")
    search_fields = ("error_type", "error_message", "endpoint", "user_email", "component")
    readonly_fields = (
        "timestamp", "last_seen", "occurrences", "fingerprint",
        "source", "severity", "error_type", "error_message",
        "endpoint", "method", "status_code", "user", "user_email",
        "ip_address", "user_agent", "referer", "traceback", "component", "extra",
    )
    actions = ["mark_resolved"]
    date_hierarchy = "last_seen"
    list_per_page = 50

    @admin.action(description="Mark selected errors as resolved")
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(resolved=True, acknowledged_by=request.user,
                        acknowledged_at=timezone.now())


@admin.register(HealthSample)
class HealthSampleAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "source", "db_ok", "cache_ok", "storage_ok",
                    "ml_ok", "disk_used_pct", "error_rate_5min")
    list_filter = ("source", "db_ok", "storage_ok")
    readonly_fields = tuple(f.name for f in HealthSample._meta.get_fields())
    date_hierarchy = "timestamp"
    list_per_page = 50
