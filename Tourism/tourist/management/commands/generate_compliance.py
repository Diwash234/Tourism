"""
Management command to generate a compliance document.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a compliance document"

    def handle(self, *args, **options):
        self.stdout.write("Generating compliance document...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Compliance

## GDPR

- Right to access: Users can export their data
- Right to erasure: Users can delete their account
- Data minimization: Only collect necessary data
- Consent: Clear consent for data processing

## Data Retention

- User data: Until account deletion
- Audit logs: 90 days
- Error events: 90 days
- Analytics: 2 years

## Security

- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- Access control: RBAC
- Audit logging: All actions logged
"""

        with open(docs_dir / "COMPLIANCE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Compliance document generated at {docs_dir / 'COMPLIANCE.md'}"))
