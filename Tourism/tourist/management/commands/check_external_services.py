"""
Management command to check external service connectivity.
"""
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Check connectivity to external services"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("EXTERNAL SERVICE CONNECTIVITY CHECK")
        self.stdout.write("=" * 60)

        services = {
            "Google OAuth": "https://accounts.google.com",
            "GitHub OAuth": "https://github.com",
            "OpenWeatherMap": "https://api.openweathermap.org",
            "Overpass API": "https://overpass-api.de/api/status",
            "Wikimedia Commons": "https://commons.wikimedia.org",
            "ML Service": settings.ML_SERVICE_URL,
        }

        for name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {name}: {url}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  [WARN] {name}: {url} (HTTP {response.status_code})"))
            except requests.RequestException as exc:
                self.stdout.write(self.style.ERROR(f"  [FAIL] {name}: {url} ({exc})"))

        self.stdout.write("=" * 60)
