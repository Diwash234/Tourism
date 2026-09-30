"""
Management command to generate a Fluentd configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Fluentd configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Fluentd configuration...")

        content = """<source>
  @type forward
  port 24224
</source>

<match tourism.**>
  @type elasticsearch
  host localhost
  port 9200
  logstash_format true
  logstash_prefix tourism
</match>
"""

        with open(Path("fluentd.conf"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Fluentd configuration generated at fluentd.conf"))
