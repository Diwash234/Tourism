"""
Management command to generate responsible disclosure policy.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate responsible disclosure policy"

    def handle(self, *args, **options):
        self.stdout.write("Generating responsible disclosure policy...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Responsible Disclosure Policy

## Philosophy

We believe in working with security researchers to improve our security.

## Guidelines

1. Do not access or modify user data
2. Do not disrupt our services
3. Give us reasonable time to respond
4. Act in good faith

## Reporting

Email: security@example.com

## Recognition

We will credit researchers in our security advisories.
"""

        with open(docs_dir / "RESPONSIBLE_DISCLOSURE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Responsible disclosure policy generated at {docs_dir / 'RESPONSIBLE_DISCLOSURE.md'}"))
