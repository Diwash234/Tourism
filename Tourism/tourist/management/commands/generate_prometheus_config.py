"""
Management command to generate a Prometheus configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Prometheus configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Prometheus configuration...")

        content = """# Prometheus Configuration
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
"""

        with open(Path("prometheus.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Prometheus configuration generated at prometheus.yml"))
