from rest_framework import serializers

from .models import Notification, DeviceToken


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "channel", "title", "message", "is_read", "is_sent", "related_alert", "created_at"]
        read_only_fields = ["channel", "title", "message", "is_sent", "related_alert", "created_at"]


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "token", "platform", "created_at"]