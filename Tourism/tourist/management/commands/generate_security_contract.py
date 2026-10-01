"""
Management command to generate security contract template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security contract template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security contract template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Contract

## Parties

- Client: [Client Name]
- Provider: Nepal Tourism Platform

## Services

- Security monitoring
- Incident response
- Vulnerability management
- Compliance support

## Terms

### Payment
Monthly fees due on the 1st of each month.

### Term
Initial term of 1 year, auto-renewing.

### Termination
Either party may terminate with 30 days notice.

## Signatures

Client: _________________ Date: _________
Provider: _________________ Date: _________
"""

        with open(docs_dir / "CONTRACT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security contract template generated at {docs_dir / 'CONTRACT.md'}"))
