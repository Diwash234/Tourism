"""
Management command to generate a risk assessment.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a risk assessment"

    def handle(self, *args, **options):
        self.stdout.write("Generating risk assessment...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Risk Assessment

## Risk Matrix

| Risk | Likelihood | Impact | Score | Mitigation |
|------|------------|--------|-------|------------|
| Data breach | Medium | High | 6 | Encryption, access control |
| DDoS attack | Medium | High | 6 | Rate limiting, CDN |
| SQL injection | Low | High | 3 | Parameterized queries |
| XSS | Low | Medium | 2 | Output encoding |
| Insider threat | Low | High | 3 | RBAC, audit logging |

## Risk Levels

- **Critical (9-12):** Immediate action required
- **High (6-8):** Action required within 30 days
- **Medium (3-5):** Action required within 90 days
- **Low (1-2):** Monitor and review annually
"""

        with open(docs_dir / "RISK_ASSESSMENT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Risk assessment generated at {docs_dir / 'RISK_ASSESSMENT.md'}"))
