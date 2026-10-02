"""
Management command to generate security CIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security CIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security CIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Confidentiality, Integrity, Availability Assessment

## Confidentiality

| Asset | Sensitivity | Controls | Rating |
|-------|-------------|----------|--------|
| | | | |

## Integrity

| Asset | Criticality | Controls | Rating |
|-------|-------------|----------|--------|
| | | | |

## Availability

| Service | Criticality | Controls | Rating |
|---------|-------------|----------|--------|
| | | | |

## Overall Assessment

- **Confidentiality:** [rating]
- **Integrity:** [rating]
- **Availability:** [rating]
- **Overall:** [rating]
"""

        with open(docs_dir / "CIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security CIA template generated at {docs_dir / 'CIA.md'}"))
