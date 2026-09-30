"""
Management command to generate security compliance framework.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security compliance framework"

    def handle(self, *args, **options):
        self.stdout.write("Generating security compliance framework...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Compliance Framework

## Standards

### ISO 27001
- Information security management
- Risk assessment
- Security controls

### SOC 2
- Security
- Availability
- Confidentiality

### GDPR
- Data protection
- Privacy rights
- Consent management

## Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Access Control | RBAC | Implemented |
| Encryption | AES-256 | Implemented |
| Logging | Audit logs | Implemented |
| Backup | Daily | Implemented |
| Monitoring | Prometheus | Implemented |
"""

        with open(docs_dir / "COMPLIANCE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security compliance framework generated at {docs_dir / 'COMPLIANCE.md'}"))
