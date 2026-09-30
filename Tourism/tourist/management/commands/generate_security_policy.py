"""
Management command to generate a security policy.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a security policy"

    def handle(self, *args, **options):
        self.stdout.write("Generating security policy...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Policy

## Reporting Vulnerabilities

Please report security vulnerabilities to: security@your-domain.com

## Scope

- Web application
- API endpoints
- Mobile applications
- Infrastructure

## Response Process

1. Acknowledge receipt within 24 hours
2. Investigate and validate
3. Develop and deploy fix
4. Credit reporter (with permission)

## Safe Harbor

We will not take legal action against researchers who:
- Follow responsible disclosure
- Do not access or modify user data
- Do not disrupt service availability
"""

        with open(docs_dir / "SECURITY_POLICY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security policy generated at {docs_dir / 'SECURITY_POLICY.md'}"))
