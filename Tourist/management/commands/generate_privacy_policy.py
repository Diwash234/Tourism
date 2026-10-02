"""
Management command to generate privacy policy.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate privacy policy"

    def handle(self, *args, **options):
        self.stdout.write("Generating privacy policy...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Privacy Policy

## Data We Collect

- Email address
- Name
- Phone number (optional)
- Location data (with consent)
- Travel preferences

## How We Use Your Data

- Provide personalized recommendations
- Improve our services
- Send important notifications
- Ensure safety during travel

## Data Sharing

We do not sell your personal data. We share data with:
- Service providers (hosting, analytics)
- Emergency services (when required by law)

## Your Rights

- Access your data
- Correct your data
- Delete your data
- Export your data
- Withdraw consent

## Contact

For privacy inquiries, contact: privacy@example.com
"""

        with open(docs_dir / "PRIVACY_POLICY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Privacy policy generated at {docs_dir / 'PRIVACY_POLICY.md'}"))
