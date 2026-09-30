"""
Management command to generate security ROPA template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security ROPA template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security ROPA template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Record of Processing Activities

## Controller Information

- Name: Nepal Tourism Platform
- Contact: dpo@your-domain.com

## Processing Activities

| Activity | Purpose | Data Categories | Data Subjects | Retention |
|----------|---------|-----------------|---------------|-----------|
| User accounts | Authentication | Email, name | Users | Account lifetime |
| Reviews | Content | Comments, ratings | Users | 2 years |
| Analytics | Improvement | Usage data | Users | 1 year |

## Recipients

- Internal: Development team
- External: Hosting provider, analytics provider

## International Transfers

- None / SCCs in place
"""

        with open(docs_dir / "ROPA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security ROPA template generated at {docs_dir / 'ROPA.md'}"))
