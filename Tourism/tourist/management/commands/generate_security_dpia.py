"""
Management command to generate DPIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate DPIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating DPIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Data Protection Impact Assessment Template

## 1. Project Overview

- **Project Name:**
- **Date:**
- **Assessor:**
- **Version:**

## 2. Data Processing Description

- **Nature of processing:**
- **Scope of processing:**
- **Context of processing:**
- **Purpose of processing:**

## 3. Necessity and Proportionality

- **Is processing necessary?**
- **Is it proportionate to the purpose?**
- **Alternatives considered:**

## 4. Risks to Data Subjects

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| | | | |

## 5. Compliance Measures

- [ ] Lawful basis identified
- [ ] Data minimization
- [ ] Purpose limitation
- [ ] Storage limitation
- [ ] Security measures
- [ ] Data subject rights

## 6. Consultation

- [ ] DPO consulted
- [ ] Data subjects consulted
- [ ] Other stakeholders consulted

## 7. Conclusion

- **Overall risk level:**
- **Approval required:**
- **Review date:**
"""

        with open(docs_dir / "DPIA_TEMPLATE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"DPIA template generated at {docs_dir / 'DPIA_TEMPLATE.md'}"))
