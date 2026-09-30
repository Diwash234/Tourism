"""
Management command to generate a threat model.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a threat model"

    def handle(self, *args, **options):
        self.stdout.write("Generating threat model...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Threat Model

## Assets

- User data (PII)
- Authentication credentials
- Payment information
- Application source code
- Infrastructure

## Threats

### STRIDE Analysis

| Threat | Description | Mitigation |
|--------|-------------|------------|
| Spoofing | Impersonating users | JWT tokens, MFA |
| Tampering | Modifying data | Input validation, signatures |
| Repudiation | Denying actions | Audit logging |
| Information Disclosure | Leaking data | Encryption, access control |
| Denial of Service | Service disruption | Rate limiting, scaling |
| Elevation of Privilege | Unauthorized access | RBAC, permissions |

## Attack Surface

- Web application
- API endpoints
- Admin panel
- Third-party integrations
"""

        with open(docs_dir / "THREAT_MODEL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Threat model generated at {docs_dir / 'THREAT_MODEL.md'}"))
