"""
Management command to generate a security report.
"""
from django.core.management.base import BaseCommand
from tourist.models import User, AuditLog


class Command(BaseCommand):
    help = "Generate a security report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SECURITY REPORT")
        self.stdout.write("=" * 60)

        # Failed login attempts
        self.stdout.write("\nFailed Login Attempts (last 24h):")
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(hours=24)
        failed_logins = AuditLog.objects.filter(
            action="auth.login",
            severity="warning",
            created_at__gte=cutoff,
        ).count()
        self.stdout.write(f"  Failed logins: {failed_logins}")

        # Inactive admin accounts
        self.stdout.write("\nInactive Admin Accounts:")
        admins = User.objects.filter(is_staff=True, is_active=True)
        inactive_admins = admins.filter(last_login__lt=cutoff)
        self.stdout.write(f"  Total admins: {admins.count()}")
        self.stdout.write(f"  Inactive (24h): {inactive_admins.count()}")

        # Unverified users
        self.stdout.write("\nUnverified Users:")
        unverified = User.objects.filter(is_verified=False).count()
        self.stdout.write(f"  Total unverified: {unverified}")

        self.stdout.write("\n" + "=" * 60)
