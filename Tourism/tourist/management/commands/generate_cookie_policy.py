"""
Management command to generate cookie policy.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate cookie policy"

    def handle(self, *args, **options):
        self.stdout.write("Generating cookie policy...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Cookie Policy

## What Are Cookies

Cookies are small text files stored on your device.

## How We Use Cookies

### Essential Cookies
- Authentication
- Security
- Session management

### Analytics Cookies
- Usage tracking
- Performance monitoring

### Preference Cookies
- Language preference
- Theme selection

## Managing Cookies

You can control cookies through your browser settings.
"""

        with open(docs_dir / "COOKIE_POLICY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Cookie policy generated at {docs_dir / 'COOKIE_POLICY.md'}"))
