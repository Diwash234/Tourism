"""
Management command to generate SLA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate SLA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating SLA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Service Level Agreement

## Service Availability

- Uptime guarantee: 99.9%
- Maintenance windows: Sundays 2-4 AM UTC
- Planned downtime notice: 48 hours

## Incident Response

| Severity | Response Time | Resolution Time |
|----------|---------------|-----------------|
| Critical | 15 minutes | 4 hours |
| High | 30 minutes | 8 hours |
| Medium | 2 hours | 24 hours |
| Low | 8 hours | 72 hours |

## Compliance

- GDPR compliant
- ISO 27001 certified
- SOC 2 Type II audited
"""

        with open(docs_dir / "SLA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"SLA template generated at {docs_dir / 'SLA.md'}"))
