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
- Travel preferences

## Threats

### STRIDE Analysis

| Threat | Description | Mitigation |
|--------|-------------|------------|
| Spoofing | Impersonating users | MFA, strong auth |
| Tampering | Modifying data | Input validation, encryption |
| Repudiation | Denying actions | Audit logging |
| Information Disclosure | Leaking data | Encryption, access control |
| Denial of Service | Disrupting service | Rate limiting, scaling |
| Elevation of Privilege | Gaining unauthorized access | RBAC, least privilege |

## Attack Surface

- Web application
- API endpoints
- Network communications
- Third-party integrations

## Risk Assessment

| Risk | Likelihood | Impact | Score |
|------|------------|--------|-------|
| Data breach | Medium | High | 6 |
| DDoS attack | Low | Medium | 2 |
| Insider threat | Low | High | 2 |
"""

        with open(docs_dir / "THREAT_MODEL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Threat model generated at {docs_dir / 'THREAT_MODEL.md'}"))
