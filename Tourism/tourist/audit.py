"""
Enhanced audit logging utilities.
"""
import json
import logging
import time
import uuid
from typing import Any, Optional

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """Enhanced audit log for tracking all system actions."""
    id = models.BigAutoField(primary_key=True)
    request_id = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey("tourist.User", on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(blank=True)
    action = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=50, db_index=True)
    severity = models.CharField(max_length=20, default="info")
    source = models.CharField(max_length=20, default="backend")
    endpoint = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=10, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    message = models.TextField(blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    duration_ms = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["category", "created_at"]),
            models.Index(fields=["severity", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.user_email} at {self.created_at}"


class ErrorEvent(models.Model):
    """Enhanced error event tracking."""
    id = models.BigAutoField(primary_key=True)
    request_id = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey("tourist.User", on_delete=models.SET_NULL, null=True, blank=True)
    exception_type = models.CharField(max_length=100)
    exception_message = models.TextField()
    traceback = models.TextField(blank=True)
    endpoint = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=10, blank=True)
    status_code = models.IntegerField(default=500)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["exception_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.exception_type}: {self.exception_message[:100]}"
