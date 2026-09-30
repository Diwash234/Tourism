"""
Management command to generate a deployment checklist.
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Generate a deployment checklist"

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("DEPLOYMENT CHECKLIST")
        self.stdout.write("=" * 70)

        checks = [
            ("DEBUG is False", not settings.DEBUG),
            ("SECRET_KEY is set", bool(settings.SECRET_KEY)),
            ("ALLOWED_HOSTS is configured", bool(settings.ALLOWED_HOSTS)),
            ("CORS_ALLOWED_ORIGINS is set", bool(settings.CORS_ALLOWED_ORIGINS)),
            ("CSRF_TRUSTED_ORIGINS is set", bool(settings.CSRF_TRUSTED_ORIGINS)),
            ("DATABASE_URL is set", bool(settings.DATABASES["default"].get("NAME"))),
            ("EMAIL_BACKEND is configured", bool(settings.EMAIL_BACKEND)),
            ("OAuth Google is configured", bool(settings.GOOGLE_CLIENT_ID)),
            ("OAuth GitHub is configured", bool(settings.GITHUB_CLIENT_ID)),
            ("ML_SERVICE_URL is set", bool(settings.ML_SERVICE_URL)),
            ("IMAGE_BASE_URL is set", bool(settings.IMAGE_BASE_URL)),
        ]

        self.stdout.write("\nPre-deployment checks:")
        for check_name, passed in checks:
            status = "PASS" if passed else "FAIL"
            style = self.style.SUCCESS if passed else self.style.ERROR
            self.stdout.write(style(f"  [{status}] {check_name}"))

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("Make sure all checks pass before deploying to production!")
        self.stdout.write("=" * 70)
