"""
Management command to generate a security checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a security checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating security checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Checklist

## Authentication
- [ ] Strong password policy
- [ ] Multi-factor authentication
- [ ] Session management
- [ ] OAuth implementation

## Authorization
- [ ] Role-based access control
- [ ] Object-level permissions
- [ ] Access review

## Data Protection
- [ ] Encryption at rest
- [ ] Encryption in transit
- [ ] Data classification
- [ ] Data retention

## Infrastructure
- [ ] Firewalls
- [ ] IDS/IPS
- [ ] Monitoring
- [ ] Incident Response

## Application Security
- [ ] Secure coding
- [ ] Code review
- [ ] Penetration testing
- [ ] Vulnerability scanning

## Compliance
- [ ] GDPR
- [ ] ISO 27001
- [ ] SOC 2
- [ ] PCI DSS
"""

        with open(docs_dir / "CHECKLIST.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security checklist generated at {docs_dir / 'CHECKLIST.md'}"))
