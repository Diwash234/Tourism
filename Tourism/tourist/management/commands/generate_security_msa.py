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

- **Client:** [Client Name]
- **Provider:** [Provider Name]

### Services
- Security services
- Support services
- Consulting services

### Terms
- Payment terms: Net 30
- Renewal: Automatic
- Termination: 30 days notice

### Liability
- Limitation of liability
- Indemnification
- Insurance requirements

### Governing Law
This agreement is governed by the laws of [Jurisdiction].

### Signatures

**Client:** _________________ Date: _________

**Provider:** _________________ Date: _________
"""

        with open(docs_dir / "MSA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security MSA template generated at {docs_dir / 'MSA.md'}"))
