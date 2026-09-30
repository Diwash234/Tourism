"""
Management command to generate LIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate LIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating LIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Legitimate Interest Assessment Template

## 1. Purpose

- **Legitimate interest:**
- **Business benefit:**
- **Necessity:**

## 2. Necessity Test

- **Is processing necessary?**
- **Is it proportionate?**
- **Alternatives considered:**

## 3. Balancing Test

| Interest | Weight | Data Subject Rights | Weight |
|----------|--------|---------------------|--------|
| | | | |

## 4. Safeguards

- **Technical measures:**
- **Organizational measures:**
- **Opt-out mechanism:**

## 5. Conclusion

- **Overall assessment:**
- **Approval:**
- **Review date:**
"""

        with open(docs_dir / "LIA_TEMPLATE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"LIA template generated at {docs_dir / 'LIA_TEMPLATE.md'}"))
