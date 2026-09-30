"""
Management command to generate security budget template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security budget template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security budget template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Budget

## Personnel
- Security team salaries
- Training and certification
- Contractors

## Tools
- SIEM solution
- Vulnerability scanner
- Penetration testing
- Security monitoring

## Infrastructure
- Firewall
- WAF
- DDoS protection
- Backup systems

## Services
- Security consulting
- Compliance audits
- Incident response retainer

## Total
- Annual budget: $XXX,XXX
"""

        with open(docs_dir / "BUDGET.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security budget template generated at {docs_dir / 'BUDGET.md'}"))
