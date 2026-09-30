"""
Management command to generate security governance framework.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security governance framework"

    def handle(self, *args, **options):
        self.stdout.write("Generating security governance framework...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Governance Framework

## Roles and Responsibilities

### CISO
- Overall security strategy
- Risk management
- Compliance oversight

### Security Team
- Security operations
- Incident response
- Vulnerability management

### Development Team
- Secure coding practices
- Code reviews
- Security testing

### Operations Team
- Infrastructure security
- Monitoring
- Incident detection

## Policies

1. Acceptable Use Policy
2. Access Control Policy
3. Data Protection Policy
4. Incident Response Policy
5. Change Management Policy

## Review Cycle

- Policies: Annual review
- Risk assessment: Quarterly
- Penetration test: Annual
- Security training: Annual
"""

        with open(docs_dir / "GOVERNANCE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security governance framework generated at {docs_dir / 'GOVERNANCE.md'}"))
