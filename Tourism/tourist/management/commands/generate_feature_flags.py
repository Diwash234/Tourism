"""
Management command to generate a feature flags report.
"""
from django.core.management.base import BaseCommand
from tourist.config import FeatureFlags


class Command(BaseCommand):
    help = "Generate a feature flags report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("FEATURE FLAGS REPORT")
        self.stdout.write("=" * 60)

        flags = FeatureFlags.get_all()
        for feature, enabled in flags.items():
            status = "ENABLED" if enabled else "DISABLED"
            style = self.style.SUCCESS if enabled else self.style.WARNING
            self.stdout.write(style(f"  {feature}: {status}"))

        self.stdout.write("\n" + "=" * 60)
