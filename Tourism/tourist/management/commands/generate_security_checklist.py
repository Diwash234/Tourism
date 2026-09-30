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
- [ ] API rate limiting

## Data Protection
- [ ] Encryption at rest
- [ ] Encryption in transit
- [ ] Data minimization
- [ ] Secure deletion

## Infrastructure
- [ ] Firewall configuration
- [ ] DDoS protection
- [ ] Regular backups
- [ ] Monitoring and alerting

## Application Security
- [ ] Input validation
- [ ] Output encoding
- [ ] CSRF protection
- [ ] XSS prevention
- [ ] SQL injection prevention

## Incident Response
- [ ] Incident response plan
- [ ] Communication plan
- [ ] Post-incident review
"""

        with open(docs_dir / "CHECKLIST.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security checklist generated at {docs_dir / 'CHECKLIST.md'}"))
