"""
Management command to generate security TIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security TIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security TIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Transfer Impact Assessment

## Transfer Details

- Data exporter: [Exporter]
- Data importer: Nepal Tourism Platform
- Destination country: [Country]

## Legal Framework

- Adequacy decision: [yes/no]
- Appropriate safeguards: [list]

## Assessment

| Factor | Finding | Risk |
|--------|---------|------|
| Government access | [finding] | [risk] |
| Judicial redress | [finding] | [risk] |
| Data protection laws | [finding] | [risk] |

## Conclusion

[Overall assessment and recommendations]
"""

        with open(docs_dir / "TIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security TIA template generated at {docs_dir / 'TIA.md'}"))
