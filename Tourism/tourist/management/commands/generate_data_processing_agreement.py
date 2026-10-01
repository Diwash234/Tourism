"""
Management command to generate a data processing agreement.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a data processing agreement"

    def handle(self, *args, **options):
        self.stdout.write("Generating data processing agreement...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Data Processing Agreement

## Parties

- Data Controller: Nepal Tourism Platform
- Data Processor: [Processor Name]

## Scope

This agreement covers processing of personal data on behalf of the controller.

## Obligations

### Processor shall:
- Process data only on documented instructions
- Implement appropriate security measures
- Assist with data subject rights requests
- Delete data after service ends

### Controller shall:
- Provide clear processing instructions
- Ensure lawful basis for processing

## Sub-processors

Any sub-processors must be approved by the controller in writing.
"""

        with open(docs_dir / "DATA_PROCESSING_AGREEMENT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Data processing agreement generated at {docs_dir / 'DATA_PROCESSING_AGREEMENT.md'}"))
