"""
Management command to generate TIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate TIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating TIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Transfer Impact Assessment Template

## 1. Transfer Details

- **Data exporter:**
- **Data importer:**
- **Destination country:**
- **Date:**

## 2. Data Being Transferred

- **Categories of data:**
- **Volume of data:**
- **Frequency of transfer:**
- **Sensitivity of data:**

## 3. Legal Framework

- **Adequacy decision:** [yes/no]
- **Appropriate safeguards:** [list]
- **Derogations:** [list]

## 4. Assessment

| Factor | Finding | Risk Level |
|--------|---------|------------|
| Government access | | |
| Judicial redress | | |
| Data protection laws | | |
| Oversight mechanisms | | |

## 5. Supplementary Measures

- **Technical measures:**
- **Organizational measures:**
- **Contractual measures:**

## 6. Conclusion

- **Overall risk:**
- **Approval:**
- **Review date:**
"""

        with open(docs_dir / "TIA_TEMPLATE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"TIA template generated at {docs_dir / 'TIA_TEMPLATE.md'}"))
