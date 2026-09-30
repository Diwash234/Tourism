"""
Management command to generate a Kibana dashboard.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Kibana dashboard"

    def handle(self, *args, **options):
        self.stdout.write("Generating Kibana dashboard...")

        dashboard = {
            "version": "8.0.0",
            "objects": [
                {
                    "id": "tourism-dashboard",
                    "type": "dashboard",
                    "attributes": {
                        "title": "Nepal Tourism Platform",
                        "panels": [
                            {
                                "id": "api-requests",
                                "type": "visualization",
                                "panelIndex": 1,
                            },
                        ],
                    },
                }
            ]
        }

        with open(Path("kibana_dashboard.json"), "w") as f:
            json.dump(dashboard, f, indent=2)

        self.stdout.write(self.style.SUCCESS("Kibana dashboard generated at kibana_dashboard.json"))
