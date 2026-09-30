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

## Processing Activity

- Activity: [description]
- Purpose: [purpose]
- Legal basis: [basis]

## Necessity and Proportionality

- Is processing necessary? [yes/no]
- Is it proportionate? [yes/no]
- Alternatives considered? [list]

## Risks to Data Subjects

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Privacy violation | Low | High | Encryption |
| Data breach | Low | High | Access controls |

## Conclusion

[Overall assessment and recommendations]
"""

        with open(docs_dir / "DPIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security DPIA template generated at {docs_dir / 'DPIA.md'}"))
