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

- **Disclosing Party:** [Party Name]
- **Receiving Party:** [Party Name]

## Definition

Confidential Information includes all non-public information shared between parties.

## Obligations

The Receiving Party agrees to:
- Maintain confidentiality
- Not disclose to third parties
- Use only for intended purpose

## Exceptions

This agreement does not apply to information that:
- Is publicly available
- Is independently developed
- Is required to be disclosed by law

## Term

This agreement is effective for two years from the date of signature.

## Remedies

Breach of this agreement may result in legal action.

## Signatures

**Disclosing Party:** _________________ Date: _________

**Receiving Party:** _________________ Date: _________
"""

        with open(docs_dir / "NDA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security NDA template generated at {docs_dir / 'NDA.md'}"))
