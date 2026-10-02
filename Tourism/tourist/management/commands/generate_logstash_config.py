"""
Management command to generate a Logstash configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Logstash configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Logstash configuration...")

        content = """input {
  beats {
    port => 5044
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "tourism-logs-%{+YYYY.MM.dd}"
  }
}
"""

        with open(Path("logstash.conf"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Logstash configuration generated at logstash.conf"))
