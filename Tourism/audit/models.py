"""
audit/models.py
----------------
Central audit + error logging. Every important backend event, unhandled
exception, and frontend crash/error lands here so mistakes are easy to find.

Three models:
  * AuditLog     – human/system actions (created/updated/deleted records,
                   admin logins, permission changes, payment events, etc.)
  * ErrorEvent   – backend exceptions + frontend JS errors reported by the
                   React ErrorBoundary / logger (status_code, stack trace,
                   endpoint, user, request metadata).
  * HealthSample – point-in-time health snapshots written by the
                   system_health app (db/cache/disk latency, error rate).
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


# ---- Severity & category enums shared across audit + health ---------------
class Severity:
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    CHOICES = [
        (DEBUG, "Debug"),
        (INFO, "Info"),
        (WARNING, "Warning"),
        (ERROR, "Error"),
        (CRITICAL, "Critical"),
    ]


class ActionCategory:
    AUTH = "auth"
    DATA = "data"
    ADMIN = "admin"
    SECURITY = "security"
    PAYMENT = "payment"
    MEDIA = "media"
    ML = "ml"
    SYSTEM = "system"
    FRONTEND = "frontend"
    OTHER = "other"

    CHOICES = [
        (AUTH, "Authentication"),
        (DATA, "Data change"),
        (ADMIN, "Admin action"),
        (SECURITY, "Security"),
        (PAYMENT, "Payment"),
        (MEDIA, "Media/Image"),
        (ML, "ML / AI"),
        (SYSTEM, "System"),
        (FRONTEND, "Frontend"),
        (OTHER, "Other"),
    ]


class Source:
    BACKEND = "backend"
    FRONTEND = "frontend"
    CELERY = "celery"
    CRON = "cron"
    EXTERNAL = "external"

    CHOICES = [
        (BACKEND, "Backend"),
        (FRONTEND, "Frontend"),
        (CELERY, "Worker/Celery"),
        (CRON, "Scheduled task"),
        (EXTERNAL, "External webhook"),
    ]


class AuditLog(models.Model):
    """Structured event log for any notable action in the system."""

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="audit_entries",
    )
    user_email = models.EmailField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    actor_role = models.CharField(max_length=32, blank=True, null=True)

    category = models.CharField(max_length=16, choices=ActionCategory.CHOICES,
                                default=ActionCategory.OTHER, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.CHOICES,
                                default=Severity.INFO, db_index=True)
    source = models.CharField(max_length=16, choices=Source.CHOICES,
                              default=Source.BACKEND, db_index=True)

    action = models.CharField(max_length=120, db_index=True)  # e.g. "destination.create"
    message = models.TextField(blank=True)
    object_type = models.CharField(max_length=120, blank=True, db_index=True)
    object_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    endpoint = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    status_code = models.PositiveSmallIntegerField(blank=True, null=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["category", "severity"]),
            models.Index(fields=["object_type", "object_id"]),
        ]
        verbose_name = "Audit log entry"
        verbose_name_plural = "Audit log entries"

    def __str__(self):
        return f"[{self.severity.upper()}] {self.action} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"


class ErrorEvent(models.Model):
    """
    All unhandled backend exceptions + frontend-reported JS errors end up
    here. Duplicates (same fingerprint within 5 minutes) are merged into
    `occurrences` rather than creating rows per hit to keep the table sane.
    """

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)
    occurrences = models.PositiveIntegerField(default=1)
    resolved = models.BooleanField(default=False, db_index=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="acknowledged_errors",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)

    source = models.CharField(max_length=16, choices=Source.CHOICES,
                              default=Source.BACKEND, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.CHOICES,
                                default=Severity.ERROR, db_index=True)
    error_type = models.CharField(max_length=120, db_index=True)  # e.g. ValueError, ChunkLoadError
    error_message = models.TextField(blank=True)
    fingerprint = models.CharField(max_length=120, db_index=True)  # hash(type+endpoint+message[:80])

    # Request context
    endpoint = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    status_code = models.PositiveSmallIntegerField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="error_events",
    )
    user_email = models.EmailField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True, null=True)

    traceback = models.TextField(blank=True)          # backend exception / frontend stack
    component = models.CharField(max_length=160, blank=True, null=True)  # React component / python module
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["-last_seen"]),
            models.Index(fields=["source", "resolved", "severity"]),
        ]
        verbose_name = "Error event"
        verbose_name_plural = "Error events"

    def __str__(self):
        return f"{self.error_type}: {self.error_message[:80]} ({self.occurrences}x)"


class HealthSample(models.Model):
    """Time-series snapshots of system vitals written every N minutes."""

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=32, default="django")

    # Boolean checks
    db_ok = models.BooleanField(default=True)
    cache_ok = models.BooleanField(default=True)
    storage_ok = models.BooleanField(default=True)
    ml_ok = models.BooleanField(null=True, blank=True)
    overpass_ok = models.BooleanField(null=True, blank=True)
    media_storage_ok = models.BooleanField(default=True)

    # Latencies / counters
    db_latency_ms = models.FloatField(null=True, blank=True)
    api_p95_ms = models.FloatField(null=True, blank=True)
    disk_used_pct = models.FloatField(null=True, blank=True)
    memory_used_pct = models.FloatField(null=True, blank=True)
    cpu_pct = models.FloatField(null=True, blank=True)
    error_rate_5min = models.FloatField(null=True, blank=True)

    notes = models.TextField(blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def overall(self):
        if not self.db_ok or not self.storage_ok:
            return "critical"
        if self.error_rate_5min is not None and self.error_rate_5min > 10:
            return "critical"
        if not self.cache_ok or self.ml_ok is False:
            return "warning"
        if self.error_rate_5min is not None and self.error_rate_5min > 2:
            return "warning"
        return "ok"
