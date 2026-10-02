"""
Management command to clean up old data.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tourist.models import AuditLog, ErrorEvent, Notification


class Command(BaseCommand):
    help = "Clean up old audit logs, error events, and notifications"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete records older than this many days (default: 90)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write(f"Cleaning up records older than {days} days (before {cutoff})...")

        # Audit logs
        old_audit = AuditLog.objects.filter(created_at__lt=cutoff)
        self.stdout.write(f"  Audit logs: {old_audit.count()} records")

        # Error events
        old_errors = ErrorEvent.objects.filter(created_at__lt=cutoff)
        self.stdout.write(f"  Error events: {old_errors.count()} records")

        # Old notifications
        old_notifications = Notification.objects.filter(created_at__lt=cutoff, is_read=True)
        self.stdout.write(f"  Read notifications: {old_notifications.count()} records")

        if not dry_run:
            old_audit.delete()
            old_errors.delete()
            old_notifications.delete()
            self.stdout.write(self.style.SUCCESS("Cleanup complete."))
        else:
            self.stdout.write(self.style.WARNING("Dry run — no records were deleted."))
