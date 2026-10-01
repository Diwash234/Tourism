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

- Project name: [Name]
- Date: [Date]
- Assessor: [Name]

## Data Processing

- Purpose: [description]
- Data categories: [list]
- Data subjects: [list]
- Retention period: [period]

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Privacy violation | Low | High | Encryption |
| Data breach | Low | High | Access controls |

## Recommendations

- Implement privacy by design
- Conduct regular audits
- Provide privacy training
"""

        with open(docs_dir / "PIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security PIA template generated at {docs_dir / 'PIA.md'}"))
