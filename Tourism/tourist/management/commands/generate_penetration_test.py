"""
Management command to generate penetration test plan.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate penetration test plan"

    def handle(self, *args, **options):
        self.stdout.write("Generating penetration test plan...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Penetration Test Plan

## Scope

- Web application
- API endpoints
- Network infrastructure

## Methodology

1. **Reconnaissance** - Gather information
2. **Scanning** - Identify vulnerabilities
3. **Exploitation** - Attempt to exploit
4. **Post-Exploitation** - Assess impact
5. **Reporting** - Document findings

## Rules of Engagement

- No denial of service
- No data modification
- Business hours only
- Immediate notification of critical findings

## Deliverables

- Executive summary
- Technical findings
- Risk ratings
- Remediation recommendations
"""

        with open(docs_dir / "PENETRATION_TEST.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Penetration test plan generated at {docs_dir / 'PENETRATION_TEST.md'}"))
