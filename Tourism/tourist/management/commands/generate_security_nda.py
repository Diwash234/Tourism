"""
Management command to generate security NDA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security NDA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security NDA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Non-Disclosure Agreement

## Parties

- Disclosing Party: Nepal Tourism Platform
- Receiving Party: [Recipient Name]

## Definition

Confidential Information includes all non-public information disclosed.

## Obligations

- Maintain confidentiality
- Use only for intended purpose
- Limit access to need-to-know
- Return or destroy upon request

## Term

This agreement remains in effect for 2 years from signing.

## Signatures

Disclosing Party: _________________ Date: _________
Receiving Party: _________________ Date: _________
"""

        with open(docs_dir / "NDA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security NDA template generated at {docs_dir / 'NDA.md'}"))
