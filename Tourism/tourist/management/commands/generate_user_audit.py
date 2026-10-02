"""
Management command to generate a user audit report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import User, AuditLog


class Command(BaseCommand):
    help = "Generate a user audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("USER AUDIT REPORT")
        self.stdout.write("=" * 60)

        cutoff = timezone.now() - timedelta(days=30)

        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(last_login__gte=cutoff).count()
        new_users = User.objects.filter(date_joined__gte=cutoff).count()
        unverified = User.objects.filter(is_verified=False).count()

        self.stdout.write(f"\nTotal users: {total_users}")
        self.stdout.write(f"Active users (30d): {active_users}")
        self.stdout.write(f"New users (30d): {new_users}")
        self.stdout.write(f"Unverified users: {unverified}")

        # User roles
        self.stdout.write("\nUsers by role:")
        roles = User.objects.values("role").annotate(count=models.Count("id")).order_by("-count")
        for role in roles:
            self.stdout.write(f"  {role['role']}: {role['count']}")

        # Inactive users
        inactive = User.objects.filter(last_login__lt=cutoff).count()
        self.stdout.write(f"\nInactive users (30d+): {inactive}")

        self.stdout.write("\n" + "=" * 60)
