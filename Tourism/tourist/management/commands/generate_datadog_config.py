"""
Management command to generate a Datadog configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Datadog configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Datadog configuration...")

        content = """# Datadog Configuration
datadog:
  image: datadog/agent:latest
  environment:
    - DD_API_KEY=your-datadog-api-key
    - DD_SITE=datadoghq.com
    - DD_APM_ENABLED=true
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - /proc/:/host/proc/:ro
    - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
"""

        with open(Path("datadog.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Datadog configuration generated at datadog.yml"))
