"""
Management command to generate a Grafana dashboard.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Grafana dashboard"

    def handle(self, *args, **options):
        self.stdout.write("Generating Grafana dashboard...")

        dashboard = {
            "dashboard": {
                "title": "Nepal Tourism Platform",
                "panels": [
                    {
                        "title": "API Requests",
                        "type": "graph",
                        "targets": [{"expr": "rate(api_requests_total[5m])"}],
                    },
                    {
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [{"expr": "histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m]))"}],
                    },
                    {
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [{"expr": "rate(api_errors_total[5m])"}],
                    },
                ],
            }
        }

        with open(Path("grafana_dashboard.json"), "w") as f:
            json.dump(dashboard, f, indent=2)

        self.stdout.write(self.style.SUCCESS("Grafana dashboard generated at grafana_dashboard.json"))
