"""
Management command to generate a security FAQ.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a security FAQ"

    def handle(self, *args, **options):
        self.stdout.write("Generating security FAQ...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security FAQ

## General

### How do I report a security vulnerability?
Email security@your-domain.com with details.

### What is your disclosure policy?
We follow responsible disclosure. See our policy.

### Do you have a bug bounty program?
Yes, see our bug bounty program for details.

## Technical

### How is my data encrypted?
AES-256 at rest, TLS 1.3 in transit.

### How are passwords stored?
Bcrypt with salt.

### Do you use multi-factor authentication?
Yes, MFA is available for all accounts.
"""

        with open(docs_dir / "FAQ.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security FAQ generated at {docs_dir / 'FAQ.md'}"))
