"""
Management command to generate ROPA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate ROPA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating ROPA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Record of Processing Activities Template

## Controller Information

- **Name:**
- **Contact:**
- **DPO:**

## Processing Activity 1

- **Activity name:**
- **Purpose:**
- **Categories of data subjects:**
- **Categories of personal data:**
- **Recipients:**
- **Retention period:**
- **Security measures:**
- **Lawful basis:**

## Processing Activity 2

- **Activity name:**
- **Purpose:**
- **Categories of data subjects:**
- **Categories of personal data:**
- **Recipients:**
- **Retention period:**
- **Security measures:**
- **Lawful basis:**

## International Transfers

| Destination | Safeguards | Documentation |
|-------------|------------|---------------|
| | | |
"""

        with open(docs_dir / "ROPA_TEMPLATE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"ROPA template generated at {docs_dir / 'ROPA_TEMPLATE.md'}"))
