"""
Management command to generate security MSA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security MSA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security MSA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Master Service Agreement

## Parties

- Client: [Client Name]
- Provider: Nepal Tourism Platform

## Services

- Platform hosting and maintenance
- Security monitoring and incident response
- Data backup and recovery
- Technical support

## Terms

### Payment
Monthly fees due on the 1st of each month.

### Term
Initial term of 1 year, auto-renewing.

### Termination
Either party may terminate with 90 days notice.

## Signatures

Client: _________________ Date: _________
Provider: _________________ Date: _________
"""

        with open(docs_dir / "MSA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security MSA template generated at {docs_dir / 'MSA.md'}"))
