"""
Management command to generate security PIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security PIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security PIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Privacy Impact Assessment

## Project Information

- **Project Name:**
- **Date:**
- **Assessor:**
- **Version:**

### Description
- Purpose of processing
- Data flows
- Systems involved

### Risks
- Identified risks
- Likelihood
- Impact

### Mitigations
- Proposed measures
- Residual risk

### Approval
- Approved by:
- Date:
"""

        with open(docs_dir / "PIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security PIA template generated at {docs_dir / 'PIA.md'}"))
