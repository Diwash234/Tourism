"""
Common serializer mixins and utilities.
"""
from rest_framework import serializers


class TimestampSerializerMixin:
    """Adds created_at and updated_at fields to a serializer."""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserSerializerMixin:
    """Adds user information to a serializer."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        if hasattr(obj, "user") and obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return None


class SoftDeleteSerializerMixin:
    """Adds soft delete fields to a serializer."""

    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)


class AuditSerializerMixin:
    """Adds audit fields to a serializer."""

    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        if hasattr(obj, "created_by") and obj.created_by:
            return obj.created_by.email
        return None

    def get_updated_by(self, obj):
        if hasattr(obj, "updated_by") and obj.updated_by:
            return obj.updated_by.email
        return None
