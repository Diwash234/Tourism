"""
Management command to generate security SCC template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security SCC template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security SCC template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Standard Contractual Clauses

## Parties

- Data Exporter: [Exporter Name]
- Data Importer: Nepal Tourism Platform

## Transfer Details

- Categories of data subjects: [list]
- Categories of personal data: [list]
- Frequency of transfer: [frequency]
- Nature of processing: [description]

## Safeguards

- Technical measures: Encryption, access controls
- Organizational measures: Policies, training
- Audit rights: Annual audit permitted
"""

        with open(docs_dir / "SCC.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security SCC template generated at {docs_dir / 'SCC.md'}"))
