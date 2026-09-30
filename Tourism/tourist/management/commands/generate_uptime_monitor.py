"""
Management command to generate an uptime monitor configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an uptime monitor configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating uptime monitor configuration...")

        content = """# Uptime Monitor Configuration
monitors:
  - name: "API Health Check"
    url: "https://your-domain.com/api/v1/health/"
    interval: 60
    timeout: 10

  - name: "Frontend"
    url: "https://your-domain.com/"
    interval: 60
    timeout: 10

  - name: "Database"
    url: "https://your-domain.com/api/v1/health/detailed/"
    interval: 300
    timeout: 30

notifications:
  email:
    - admin@your-domain.com
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
"""

        with open(Path("uptime_monitor.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Uptime monitor configuration generated at uptime_monitor.yml"))
