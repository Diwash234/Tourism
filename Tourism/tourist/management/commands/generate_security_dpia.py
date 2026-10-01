"""
Management command to generate security DPIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security DPIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security DPIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Data Protection Impact Assessment

## Project Information

- **Project Name:**
- **Date:**
- **Assessor:**

### Processing
- Nature of processing
- Scope of processing
- Context of processing

### Necessity
- Purpose of processing
- Lawful basis
- Proportionality

### Risks
- Risks to rights
- Likelihood
- Severity

### Measures
- Mitigation measures
- Residual risk

### Approval
- Approved by:
- Date:
"""

        with open(docs_dir / "DPIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security DPIA template generated at {docs_dir / 'DPIA.md'}"))
