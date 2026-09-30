"""
Management command to generate a responsible disclosure policy.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a responsible disclosure policy"

    def handle(self, *args, **options):
        self.stdout.write("Generating responsible disclosure policy...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Responsible Disclosure Policy

## Philosophy

We believe in working with security researchers to improve our security.

## Guidelines

1. **Do no harm** - Don't access, modify, or delete user data
2. **Be respectful** - Don't disrupt service availability
3. **Report promptly** - Give us time to fix before public disclosure
4. **Stay in scope** - Only test systems listed in scope

## Safe Harbor

We will not pursue legal action against researchers who follow these guidelines.

## Recognition

We will credit researchers in our security advisories (with permission).
"""

        with open(docs_dir / "RESPONSIBLE_DISCLOSURE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Responsible disclosure policy generated at {docs_dir / 'RESPONSIBLE_DISCLOSURE.md'}"))
