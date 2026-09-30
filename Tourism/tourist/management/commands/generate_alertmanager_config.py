"""
Management command to generate an Alertmanager configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an Alertmanager configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Alertmanager configuration...")

        content = """global:
  smtp_smarthost: localhost:587
  smtp_from: alerts@your-domain.com

route:
  receiver: default
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: default
    email_configs:
      - to: admin@your-domain.com

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
"""

        with open(Path("alertmanager.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Alertmanager configuration generated at alertmanager.yml"))
