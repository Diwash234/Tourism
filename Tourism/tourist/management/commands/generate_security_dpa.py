"""
Management command to generate security DPA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security DPA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security DPA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Data Processing Agreement

## Parties

- **Controller:** [Controller Name]
- **Processor:** [Processor Name]

### Processing
- Purpose of processing
- Types of data
- Duration of processing

### Obligations
- Security measures
- Confidentiality
- Data subject rights

### Sub-processors
- Approval required
- Liability

### Breach Notification
- 72-hour notification
- Cooperation

### Signatures

**Controller:** _________________ Date: _________

**Processor:** _________________ Date: _________
"""

        with open(docs_dir / "DPA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security DPA template generated at {docs_dir / 'DPA.md'}"))
