"""
Management command to generate an SLO configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an SLO configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating SLO configuration...")

        content = """# Service Level Objectives Configuration
slos:
  - name: "API Availability"
    description: "Percentage of time the API is available"
    target: 99.9
    window: 30d
    burn_rate_alerts:
      - burn_rate: 2
        severity: warning
      - burn_rate: 10
        severity: critical

  - name: "Response Time"
    description: "95th percentile response time"
    target: 500ms
    window: 30d
    burn_rate_alerts:
      - burn_rate: 2
        severity: warning
      - burn_rate: 10
        severity: critical

  - name: "Error Rate"
    description: "Percentage of requests that result in errors"
    target: 0.1%
    window: 30d
    burn_rate_alerts:
      - burn_rate: 2
        severity: warning
      - burn_rate: 10
        severity: critical
"""

        with open(Path("slo.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("SLO configuration generated at slo.yml"))
