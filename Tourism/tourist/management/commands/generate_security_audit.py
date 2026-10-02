"""
Management command to generate a security audit report.
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Generate a security audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SECURITY AUDIT REPORT")
        self.stdout.write("=" * 60)

        checks = []

        # Debug mode
        if settings.DEBUG:
            checks.append(("DEBUG is enabled", False, "Set DEBUG=False in production"))
        else:
            checks.append(("DEBUG is disabled", True, ""))

        # Secret key
        if settings.SECRET_KEY and len(settings.SECRET_KEY) > 20:
            checks.append(("SECRET_KEY is strong", True, ""))
        else:
            checks.append(("SECRET_KEY is weak", False, "Use a longer, random secret key"))

        # HTTPS
        if settings.SECURE_SSL_REDIRECT:
            checks.append(("SSL redirect enabled", True, ""))
        else:
            checks.append(("SSL redirect disabled", False, "Enable SECURE_SSL_REDIRECT in production"))

        # HSTS
        if settings.SECURE_HSTS_SECONDS > 0:
            checks.append(("HSTS enabled", True, ""))
        else:
            checks.append(("HSTS disabled", False, "Enable SECURE_HSTS_SECONDS in production"))

        # Session cookie
        if settings.SESSION_COOKIE_SECURE:
            checks.append(("Session cookie secure", True, ""))
        else:
            checks.append(("Session cookie not secure", False, "Enable SESSION_COOKIE_SECURE in production"))

        # CSRF cookie
        if settings.CSRF_COOKIE_SECURE:
            checks.append(("CSRF cookie secure", True, ""))
        else:
            checks.append(("CSRF cookie not secure", False, "Enable CSRF_COOKIE_SECURE in production"))

        # Allowed hosts
        if settings.ALLOWED_HOSTS and "*" not in settings.ALLOWED_HOSTS:
            checks.append(("ALLOWED_HOSTS is specific", True, ""))
        else:
            checks.append(("ALLOWED_HOSTS is wildcard", False, "Set specific ALLOWED_HOSTS in production"))

        # CORS
        if settings.CORS_ALLOWED_ORIGINS:
            checks.append(("CORS origins configured", True, ""))
        else:
            checks.append(("CORS origins not configured", False, "Set CORS_ALLOWED_ORIGINS in production"))

        # Display results
        self.stdout.write("\nSecurity checks:")
        for check_name, passed, recommendation in checks:
            status = "PASS" if passed else "FAIL"
            style = self.style.SUCCESS if passed else self.style.ERROR
            self.stdout.write(style(f"  [{status}] {check_name}"))
            if recommendation:
                self.stdout.write(f"         → {recommendation}")

        self.stdout.write("\n" + "=" * 60)
