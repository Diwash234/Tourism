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

- Data Controller: [Client Name]
- Data Processor: Nepal Tourism Platform

## Scope

Processing of personal data as described in Annex A.

## Obligations

### Processor shall:
- Process only on documented instructions
- Implement appropriate security measures
- Assist with data subject rights
- Delete data after service ends

### Controller shall:
- Provide lawful instructions
- Ensure lawful basis for processing

## Sub-processors

List of approved sub-processors in Annex B.
"""

        with open(docs_dir / "DPA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security DPA template generated at {docs_dir / 'DPA.md'}"))
