"""
Management command to generate a user activity report.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import User, AuditLog


class Command(BaseCommand):
    help = "Generate a user activity report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to report on (default: 30)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write("=" * 60)
        self.stdout.write(f"USER ACTIVITY REPORT (last {days} days)")
        self.stdout.write("=" * 60)

        # New users
        new_users = User.objects.filter(date_joined__gte=cutoff).count()
        self.stdout.write(f"\nNew users: {new_users}")

        # Active users
        active_users = User.objects.filter(last_login__gte=cutoff).count()
        self.stdout.write(f"Active users: {active_users}")

        # Most active users
        self.stdout.write("\nMost active users:")
        active = User.objects.filter(last_login__gte=cutoff).order_by("-last_login")[:10]
        for user in active:
            self.stdout.write(f"  {user.email} — last login: {user.last_login}")

        # Audit activity
        self.stdout.write("\nAudit activity:")
        audit_count = AuditLog.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"  Total audit events: {audit_count}")

        self.stdout.write("\n" + "=" * 60)
