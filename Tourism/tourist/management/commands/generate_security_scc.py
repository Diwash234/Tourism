"""
Management command to generate security SCC template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security SCC template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security SCC template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Standard Contractual Clauses

## Parties

- **Exporter:** [Exporter Name]
- **Importer:** [Importer Name]

### Clauses
- Security measures
- Data protection
- Audit rights

### Liability
- Limitation of liability
- Indemnification

### Governing Law
This agreement is governed by the laws of [Jurisdiction].

### Signatures

**Exporter:** _________________ Date: _________

**Importer:** _________________ Date: _________
"""

        with open(docs_dir / "SCC.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security SCC template generated at {docs_dir / 'SCC.md'}"))
