"""
Management command to generate an accessibility statement.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an accessibility statement"

    def handle(self, *args, **options):
        self.stdout.write("Generating accessibility statement...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Accessibility Statement

## Commitment

We are committed to ensuring digital accessibility for people of all abilities.

## Standards

We aim to conform to WCAG 2.1 Level AA standards.

## Features

- Keyboard navigation
- Screen reader support
- High contrast mode
- Text resizing
- Alternative text for images

## Feedback

If you encounter accessibility barriers, contact: accessibility@your-domain.com
"""

        with open(docs_dir / "ACCESSIBILITY_STATEMENT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Accessibility statement generated at {docs_dir / 'ACCESSIBILITY_STATEMENT.md'}"))
