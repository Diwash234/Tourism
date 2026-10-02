"""
Management command to generate a status page configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a status page configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating status page configuration...")

        content = """# Status Page Configuration
page:
  name: "Nepal Tourism Platform"
  url: "https://status.your-domain.com"

components:
  - name: "API"
    description: "REST API"
  - name: "Frontend"
    description: "Web Application"
  - name: "Database"
    description: "PostgreSQL Database"
  - name: "Cache"
    description: "Redis Cache"
  - name: "ML Service"
    description: "Machine Learning Service"

incidents:
  - title: "API Degraded Performance"
    status: "investigating"
    impact: "minor"
    message: "We are investigating reports of slow API response times."
"""

        with open(Path("statuspage.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Status page configuration generated at statuspage.yml"))
