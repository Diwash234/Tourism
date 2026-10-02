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

1. **Perimeter** - Firewalls, WAF, DDoS protection
2. **Network** - Segmentation, VPN, monitoring
3. **Application** - Input validation, output encoding, authentication
4. **Data** - Encryption at rest and in transit
5. **Identity** - MFA, RBAC, least privilege

## Authentication Flow

1. User submits credentials
2. Server verifies credentials
3. MFA challenge (if enabled)
4. Session token issued
5. Token validated on each request

## Authorization Model

- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC)
- Object-level permissions

## Data Protection

- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Key management (HSM)
- Data classification

## Monitoring

- SIEM
- IDS/IPS
- Log analysis
- Anomaly detection
"""

        with open(docs_dir / "ARCHITECTURE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security architecture document generated at {docs_dir / 'ARCHITECTURE.md'}"))
