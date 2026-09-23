from rest_framework import serializers
from .models import AuditLog, ErrorEvent, HealthSample


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "timestamp", "user", "user_name", "user_email", "ip_address",
            "actor_role", "category", "severity", "source", "action", "message",
            "object_type", "object_id", "endpoint", "method", "status_code",
            "extra",
        ]

    def get_user_name(self, obj):
        if obj.user:
            return getattr(obj.user, "full_name", None) or (f"{obj.user.first_name} {obj.user.last_name}".strip() if obj.user.first_name else "") or obj.user.email
        return obj.user_email or "System"


class ErrorEventSerializer(serializers.ModelSerializer):
    acknowledged_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ErrorEvent
        fields = [
            "id", "timestamp", "last_seen", "occurrences", "resolved",
            "acknowledged_by", "acknowledged_by_name", "acknowledged_at",
            "resolution_note",
            "source", "severity", "error_type", "error_message", "fingerprint",
            "endpoint", "method", "status_code",
            "user", "user_email", "ip_address", "user_agent", "referer",
            "component", "traceback", "extra",
        ]
        read_only_fields = fields

    def get_acknowledged_by_name(self, obj):
        if obj.acknowledged_by:
            return getattr(obj.acknowledged_by, "full_name", None) or (f"{obj.acknowledged_by.first_name} {obj.acknowledged_by.last_name}".strip() if obj.acknowledged_by.first_name else "") or obj.acknowledged_by.email
        return None


class ErrorEventActionSerializer(serializers.Serializer):
    resolved = serializers.BooleanField(required=False)
    resolution_note = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class HealthSampleSerializer(serializers.ModelSerializer):
    overall = serializers.CharField(read_only=True)

    class Meta:
        model = HealthSample
        fields = "__all__"


class FrontendErrorSerializer(serializers.Serializer):
    """Payload the React error logger posts."""
    message = serializers.CharField(max_length=4000)
    name = serializers.CharField(max_length=120, required=False, default="FrontendError")
    stack = serializers.CharField(required=False, allow_blank=True)
    component = serializers.CharField(max_length=160, required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_null=True)
    route = serializers.CharField(required=False, allow_blank=True)
    request_id = serializers.CharField(required=False, allow_blank=True)
    extra = serializers.JSONField(required=False, default=dict)
