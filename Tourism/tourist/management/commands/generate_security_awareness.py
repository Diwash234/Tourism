"""
Management command to generate security awareness materials.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security awareness materials"

    def handle(self, *args, **options):
        self.stdout.write("Generating security awareness materials...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Awareness

## Password Security

- Use unique passwords for each account
- Use a password manager
- Enable MFA where available
- Never share passwords

## Phishing Awareness

- Verify sender email addresses
- Hover over links before clicking
- Be urgent requests for sensitive information
- Report suspicious emails

## Data Handling

- Classify data appropriately
- Store data securely
- Dispose of data properly
- Report data breaches immediately

## Physical Security

- Lock your screen when away
- Secure mobile devices
- Shred sensitive documents
- Report suspicious activity
"""

        with open(docs_dir / "AWARENESS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security awareness materials generated at {docs_dir / 'AWARENESS.md'}"))
