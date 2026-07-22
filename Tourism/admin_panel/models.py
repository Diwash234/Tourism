"""
Role-based staff management: a super admin (Django's is_superuser) assigns
specific hotels to specific staff admins to manage, and can hand out
trackable tasks. Regular staff admins only see/manage what's assigned to
them; super admins see everything.
"""
from django.conf import settings
from django.db import models


class HotelAssignment(models.Model):
    """Which staff admin is responsible for which hotel."""

    hotel = models.ForeignKey("tourist.Hotel", on_delete=models.CASCADE, related_name="staff_assignments")
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_hotels"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="hotel_assignments_made"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("hotel", "admin")
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.admin.email} -> {self.hotel.name}"


class AdminTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_tasks"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="tasks_created"
    )
    related_hotel = models.ForeignKey(
        "tourist.Hotel", on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_tasks"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-priority", "due_date", "-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.assigned_to.email} ({self.status})"