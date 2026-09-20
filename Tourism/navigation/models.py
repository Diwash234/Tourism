"""Navigation diagnostics — answer 'are users getting REAL road routes?'
without discovering later that OSRM silently failed."""
from django.db import models


class RouteDiagnostics(models.Model):
    """One row per road-route request (kept lean; prune via retention)."""

    PROVIDER_OSRM = "osrm"
    PROVIDER_GRAPH = "graphml_fallback"
    PROVIDER_LINE = "straight_line_fallback"

    provider = models.CharField(max_length=32, db_index=True)
    mode = models.CharField(max_length=16)
    distance_m = models.FloatField(null=True, blank=True)
    duration_s = models.FloatField(null=True, blank=True)
    fallback = models.BooleanField(default=False, db_index=True)
    route_time_ms = models.IntegerField(default=0)
    alternatives = models.IntegerField(default=0)
    start_lat = models.FloatField(null=True, blank=True)
    start_lng = models.FloatField(null=True, blank=True)
    dest_lat = models.FloatField(null=True, blank=True)
    dest_lng = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "route diagnostics"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider}/{self.mode} {self.distance_m}m fallback={self.fallback}"


class NavigationSession(models.Model):
    """Server-side navigation session state (recovery + analytics).

    Mirrors the frontend state machine closely enough to answer 'what is
    this user doing right now?' and to offer 'Resume navigation?' after a
    browser crash. Deliberately stores snapshots, not GPS history —
    precise location history is not retained."""

    STATUS_CHOICES = [
        ("NAVIGATING", "navigating"), ("OFF_ROUTE", "off route"),
        ("REROUTING", "rerouting"), ("ARRIVED", "arrived"),
        ("ENDED", "ended"), ("FAILED", "failed"),
    ]

    session_id = models.CharField(max_length=32, unique=True, db_index=True)
    mode = models.CharField(max_length=16, default="driving")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES,
                              default="NAVIGATING", db_index=True)
    source = models.CharField(max_length=32, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    distance_remaining_m = models.FloatField(null=True, blank=True)
    progress = models.FloatField(default=0.0)
    off_route_count = models.IntegerField(default=0)
    fix_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"nav {self.session_id} {self.status} {self.progress:.0%}"
