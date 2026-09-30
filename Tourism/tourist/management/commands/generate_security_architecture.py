"""
Management command to generate a security architecture document.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a security architecture document"

    def handle(self, *args, **options):
        self.stdout.write("Generating security architecture document...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Architecture

## Defense in Depth

1. **Perimeter** - Firewall, WAF, DDoS protection
2. **Network** - VPC, security groups, private subnets
3. **Application** - Input validation, output encoding, CSRF protection
4. **Data** - Encryption at rest and in transit
5. **Identity** - Authentication, authorization, audit logging

## Authentication Flow

1. User submits credentials
2. Server verifies credentials
3. JWT token issued
4. Token validated on each request
5. Refresh token rotation

## Data Protection

- PII encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- Database backups encrypted
- Key management via environment variables
"""

        with open(docs_dir / "ARCHITECTURE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security architecture document generated at {docs_dir / 'ARCHITECTURE.md'}"))
