"""
Management command to generate Prometheus alert rules.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate Prometheus alert rules"

    def handle(self, *args, **options):
        self.stdout.write("Generating Prometheus alert rules...")

        content = """groups:
  - name: tourism-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High response time detected

      - alert: DatabaseDown
        expr: up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Database is down

      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Redis is down
"""

        with open(Path("prometheus_alerts.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Prometheus alert rules generated at prometheus_alerts.yml"))
