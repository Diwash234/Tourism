"""
Management command to generate a Sentry configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Sentry configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Sentry configuration...")

        content = """# Sentry Configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
    environment="production",
)
"""

        with open(Path("sentry_config.py"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Sentry configuration generated at sentry_config.py"))
