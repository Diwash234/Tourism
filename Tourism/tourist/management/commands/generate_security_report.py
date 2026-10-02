"""
Management command to generate a security report.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Generate a security report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SECURITY REPORT")
        self.stdout.write("=" * 60)

        # Debug mode
        self.stdout.write("\nDebug Mode:")
        if settings.DEBUG:
            self.stdout.write(self.style.ERROR("  DEBUG is True - should be False in production"))
        else:
            self.stdout.write(self.style.SUCCESS("  DEBUG is False"))

        # HTTPS settings
        self.stdout.write("\nHTTPS Settings:")
        if settings.SECURE_SSL_REDIRECT:
            self.stdout.write(self.style.SUCCESS("  SECURE_SSL_REDIRECT is True"))
        else:
            self.stdout.write(self.style.WARNING("  SECURE_SSL_REDIRECT is False"))

        if settings.SESSION_COOKIE_SECURE:
            self.stdout.write(self.style.SUCCESS("  SESSION_COOKIE_SECURE is True"))
        else:
            self.stdout.write(self.style.WARNING("  SESSION_COOKIE_SECURE is False"))

        if settings.CSRF_COOKIE_SECURE:
            self.stdout.write(self.style.SUCCESS("  CSRF_COOKIE_SECURE is True"))
        else:
            self.stdout.write(self.style.WARNING("  CSRF_COOKIE_SECURE is False"))

        # Allowed hosts
        self.stdout.write("\nAllowed Hosts:")
        if settings.ALLOWED_HOSTS and "*" not in settings.ALLOWED_HOSTS:
            self.stdout.write(self.style.SUCCESS(f"  {', '.join(settings.ALLOWED_HOSTS)}"))
        else:
            self.stdout.write(self.style.ERROR("  ALLOWED_HOSTS is empty or contains '*'"))

        # User statistics
        self.stdout.write("\nUser Statistics:")
        total_users = User.objects.count()
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        unverified = User.objects.filter(is_verified=False).count()
        self.stdout.write(f"  Total users: {total_users}")
        self.stdout.write(f"  Staff users: {staff_users}")
        self.stdout.write(f"  Superusers: {superusers}")
        self.stdout.write(f"  Unverified users: {unverified}")

        # Inactive admin accounts
        from django.utils import timezone
        from datetime import timedelta
        inactive_admins = User.objects.filter(
            is_staff=True,
            last_login__lt=timezone.now() - timedelta(days=90)
        ).count()
        if inactive_admins:
            self.stdout.write(self.style.WARNING(f"  Inactive admin accounts (90+ days): {inactive_admins}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Security report completed")
        self.stdout.write("=" * 60)
