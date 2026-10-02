"""
Management command to generate a code of conduct.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a code of conduct"

    def handle(self, *args, **options):
        self.stdout.write("Generating code of conduct...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Code of Conduct

## Our Pledge

We pledge to make participation in our community a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

Examples of unacceptable behavior:
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without explicit permission

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project team.
"""

        with open(docs_dir / "CODE_OF_CONDUCT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Code of conduct generated at {docs_dir / 'CODE_OF_CONDUCT.md'}"))
