"""
Management command to generate a configuration report.
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Generate a configuration report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CONFIGURATION REPORT")
        self.stdout.write("=" * 60)

        # Security settings
        self.stdout.write("\n--- Security ---")
        self.stdout.write(f"  DEBUG: {settings.DEBUG}")
        self.stdout.write(f"  SECURE_SSL_REDIRECT: {settings.SECURE_SSL_REDIRECT}")
        self.stdout.write(f"  SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
        self.stdout.write(f"  CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
        self.stdout.write(f"  SECURE_HSTS_SECONDS: {settings.SECURE_HSTS_SECONDS}")

        # Database
        self.stdout.write("\n--- Database ---")
        db = settings.DATABASES["default"]
        self.stdout.write(f"  ENGINE: {db.get('ENGINE', 'N/A')}")
        self.stdout.write(f"  NAME: {db.get('NAME', 'N/A')}")

        # Cache
        self.stdout.write("\n--- Cache ---")
        cache = settings.CACHES.get("default", {})
        self.stdout.write(f"  BACKEND: {cache.get('BACKEND', 'N/A')}")

        # Email
        self.stdout.write("\n--- Email ---")
        self.stdout.write(f"  BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  HOST: {settings.EMAIL_HOST}")

        # OAuth
        self.stdout.write("\n--- OAuth ---")
        self.stdout.write(f"  Google: {'Configured' if settings.GOOGLE_CLIENT_ID else 'Not configured'}")
        self.stdout.write(f"  GitHub: {'Configured' if settings.GITHUB_CLIENT_ID else 'Not configured'}")

        self.stdout.write("\n" + "=" * 60)
