"""
Management command to generate a bug bounty program.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a bug bounty program"

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

## Eligibility

- Must be 18 years or older
- Must follow responsible disclosure
- Must not access user data

## Scope

- Web application
- API endpoints
- Mobile applications

## Exclusions

- Social engineering
- Physical attacks
- Third-party services
"""

        with open(docs_dir / "BUG_BOUNTY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Bug bounty program generated at {docs_dir / 'BUG_BOUNTY.md'}"))
