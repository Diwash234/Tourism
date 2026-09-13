"""
notifications/models.py -- moved from tourist/models.py.
db_table preserves the existing tables (real notification/device-token
data, if any) instead of starting empty under a new app label.
"""
from django.conf import settings
from django.db import models

from tourist.models import Alert, TimeStampedModel


class Notification(TimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"
        IN_APP = "in_app", "In-App"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    related_alert = models.ForeignKey(Alert, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "tourist_notification"


class DeviceToken(models.Model):
    """Push notification device tokens (FCM)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(
        max_length=10, choices=[("ios", "iOS"), ("android", "Android"), ("web", "Web")], default="web"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tourist_devicetoken"