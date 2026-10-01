"""
Management command to generate security BAA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security BAA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security BAA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Business Associate Agreement

## Parties

- **Covered Entity:** [Entity Name]
- **Business Associate:** [Associate Name]

### Services
- Description of services
- PHI handling
- Security measures

### Obligations
- Safeguards
- Breach notification
- Compliance

### Term
- Duration
- Termination

### Signatures

**Covered Entity:** _________________ Date: _________

**Business Associate:** _________________ Date: _________
"""

        with open(docs_dir / "BAA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security BAA template generated at {docs_dir / 'BAA.md'}"))
