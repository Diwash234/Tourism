"""
Management command to generate terms of service.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate terms of service"

    def handle(self, *args, **options):
        self.stdout.write("Generating terms of service...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Terms of Service

## Acceptance of Terms

By using the Nepal Tourism Platform, you agree to these terms.

## Use of Service

- You must be 18 years or older
- You are responsible for your account
- You agree to use the service lawfully

## Content

- You retain ownership of your content
- You grant us a license to display your content
- You agree not to post harmful content

## Limitation of Liability

The service is provided "as is" without warranties. We are not liable for:
- Indirect damages
- Loss of data
- Service interruptions

## Changes to Terms

We may update these terms. Continued use constitutes acceptance.
"""

        with open(docs_dir / "TERMS_OF_SERVICE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Terms of service generated at {docs_dir / 'TERMS_OF_SERVICE.md'}"))
