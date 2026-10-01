"""
Management command to generate security LIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security LIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security LIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Legitimate Interest Assessment

## Purpose

- **Legitimate interest:**
- **Business benefit:**

### Necessity
- Is processing necessary?
- Alternatives considered

### Balancing
- Individual rights
- Reasonable expectations
- Impact on individuals

### Safeguards
- Technical measures
- Organizational measures

### Conclusion
- Overall assessment:
- Approval:
"""

        with open(docs_dir / "LIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security LIA template generated at {docs_dir / 'LIA.md'}"))
