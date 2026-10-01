"""
Management command to generate a penetration test plan.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a penetration test plan"

    def handle(self, *args, **options):
        self.stdout.write("Generating penetration test plan...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Penetration Test Plan

## Scope

- Web application
- API endpoints
- Authentication system

## Methodology

1. **Reconnaissance** - Gather information
2. **Scanning** - Identify vulnerabilities
3. **Exploitation** - Attempt to exploit
4. **Post-exploitation** - Assess impact
5. **Reporting** - Document findings

## Tools

- Nmap
- Burp Suite
- OWASP ZAP
- SQLMap

## Rules of Engagement

- No denial of service
- No data modification
- Business hours only
"""

        with open(docs_dir / "PENETRATION_TEST.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Penetration test plan generated at {docs_dir / 'PENETRATION_TEST.md'}"))
