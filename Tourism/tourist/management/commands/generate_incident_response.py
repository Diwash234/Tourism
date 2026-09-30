"""
Management command to generate an incident response plan.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an incident response plan"

    def handle(self, *args, **options):
        self.stdout.write("Generating incident response plan...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Incident Response Plan

## Severity Levels

### SEV1 - Critical
- Complete service outage
- Data breach
- Response time: 15 minutes

### SEV2 - High
- Major feature broken
- Performance degradation
- Response time: 30 minutes

### SEV3 - Medium
- Minor feature broken
- Non-critical errors
- Response time: 2 hours

### SEV4 - Low
- Cosmetic issues
- Minor bugs
- Response time: 1 business day

## Response Process

1. **Detect** - Monitoring alerts or user reports
2. **Triage** - Assess severity and impact
3. **Mitigate** - Take immediate action to reduce impact
4. **Resolve** - Fix the root cause
5. **Review** - Post-incident review within 48 hours

## Communication

- Internal: Slack #incidents
- External: Status page
- Stakeholders: Email for SEV1/SEV2
"""

        with open(docs_dir / "INCIDENT_RESPONSE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Incident response plan generated at {docs_dir / 'INCIDENT_RESPONSE.md'}"))
