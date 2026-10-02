"""
Management command to generate an SLA configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an SLA configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating SLA configuration...")

        content = """# Service Level Agreement Configuration
sla:
  availability: 99.9
  response_time:
    p50: 200ms
    p95: 500ms
    p99: 1000ms
  error_rate: 0.1%

objectives:
  - name: "API Availability"
    target: 99.9
    measurement: "uptime / total_time"
  - name: "Response Time"
    target: 95
    measurement: "percentage of requests under 500ms"
  - name: "Error Rate"
    target: 0.1
    measurement: "errors / total_requests"

penalties:
  - availability: 99.0
    penalty: "10% credit"
  - availability: 95.0
    penalty: "25% credit"
"""

        with open(Path("sla.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("SLA configuration generated at sla.yml"))
