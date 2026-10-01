"""
Management command to generate security contract template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security contract template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security contract template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Contract

## Parties

- **Client:** [Client Name]
- **Provider:** [Provider Name]

## Services

### Security Services
- Security monitoring
- Incident response
- Vulnerability management
- Compliance support

### Service Levels
- Response time: 1 hour
- Resolution time: 4 hours
- Availability: 99.9%

## Responsibilities

### Client Responsibilities
- Provide access to systems
- Implement security controls
- Report security incidents

### Provider Responsibilities
- Monitor security systems
- Respond to incidents
- Provide security reports

## Confidentiality

Both parties agree to maintain confidentiality of all information shared.

## Term

This contract is effective for one year from the date of signature.

## Termination

Either party may terminate this contract with 30 days written notice.

## Signatures

**Client:** _________________ Date: _________

**Provider:** _________________ Date: _________
"""

        with open(docs_dir / "CONTRACT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security contract template generated at {docs_dir / 'CONTRACT.md'}"))
