"""
Management command to generate security LIA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security LIA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security LIA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Legitimate Interest Assessment

## Purpose

- Legitimate interest: [description]
- Business benefit: [benefit]

## Necessity Test

- Is processing necessary? [yes/no]
- Is it proportionate? [yes/no]
- Alternatives considered? [list]

## Balancing Test

| Interest | Weight | Data Subject Rights | Weight |
|----------|--------|---------------------|--------|
| [interest] | [weight] | [right] | [weight] |

## Conclusion

[Overall assessment and decision]
"""

        with open(docs_dir / "LIA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security LIA template generated at {docs_dir / 'LIA.md'}"))
