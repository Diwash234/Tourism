"""
Management command to generate a New Relic configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a New Relic configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating New Relic configuration...")

        content = """# New Relic Configuration
newrelic:
  image: newrelic/infrastructure:latest
  environment:
    - NRELIC_LICENSE_KEY=your-license-key
    - NRELIC_DISPLAY_NAME=tourism-platform
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
"""

        with open(Path("newrelic.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("New Relic configuration generated at newrelic.yml"))
