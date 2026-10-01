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

| Role | Count | Salary | Total |
|------|-------|--------|-------|
| CISO | 1 | $150,000 | $150,000 |
| Security Analysts | 3 | $80,000 | $240,000 |
| Security Engineers | 2 | $100,000 | $200,000 |
| **Total Personnel** | | | **$590,000** |

## Technology

| Item | Cost |
|------|------|
| SIEM | $50,000 |
| EDR | $30,000 |
| Firewall | $20,000 |
| IDS/IPS | $15,000 |
| Vulnerability Scanner | $10,000 |
| **Total Technology** | **$125,000** |

## Services

| Service | Cost |
|---------|------|
| Managed Security | $60,000 |
| Penetration Testing | $25,000 |
| Security Consulting | $20,000 |
| **Total Services** | **$105,000** |

## Training

| Training | Cost |
|----------|------|
| Security Awareness | $10,000 |
| Technical Training | $15,000 |
| Certification | $10,000 |
| **Total Training** | **$35,000** |

## Total Budget

| Category | Amount |
|----------|--------|
| Personnel | $590,000 |
| Technology | $125,000 |
| Services | $105,000 |
| Training | $35,000 |
| **Total** | **$855,000** |
"""

        with open(docs_dir / "BUDGET.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security budget template generated at {docs_dir / 'BUDGET.md'}"))
