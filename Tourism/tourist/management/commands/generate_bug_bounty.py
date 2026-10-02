"""
Management command to generate bug bounty program.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate bug bounty program"

    def handle(self, *args, **options):
        self.stdout.write("Generating bug bounty program...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Bug Bounty Program

## Rewards

| Severity | Reward |
|----------|--------|
| Critical | $1000+ |
| High | $500+ |
| Medium | $200+ |
| Low | $50+ |

## Scope

- Web application
- API endpoints
- Mobile applications

## Out of Scope

- Social engineering
- Physical security
- Denial of service

## How to Report

Email: security@example.com
"""

        with open(docs_dir / "BUG_BOUNTY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Bug bounty program generated at {docs_dir / 'BUG_BOUNTY.md'}"))
