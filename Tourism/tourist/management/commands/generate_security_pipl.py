"""
Management command to generate PIPL compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate PIPL compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating PIPL compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# PIPL Compliance Checklist (China)

## Consent

- [ ] Separate consent for sensitive PI
- [ ] Informed consent obtained
- [ ] Withdrawal mechanism
- [ ] Parental consent for minors under 14
- [ ] No forced consent

## Data Minimization

- [ ] Minimum necessary collection
- [ ] Purpose limitation
- [ ] Retention period defined
- [ ] Regular data review

## Cross-Border Transfer

- [ ] Security assessment by CAC
- [ ] Standard contract with recipient
- [ ] Certification by approved body
- [ ] Separate consent for transfer
- [ ] Data localization for CIIOs

## Sensitive Personal Information

- [ ] Biometric data protection
- [ ] Religious belief protection
- [ ] Specific identity protection
- [ ] Medical health protection
- [ ] Financial account protection
- [ ] Location tracking protection
- [ ] Minor data protection

## Data Subject Rights

- [ ] Right to know
- [ ] Right to decide
- [ ] Right to access/copy
- [ ] Right to correct
- [ ] Right to delete
- [ ] Right to withdraw consent
- [ ] Right to explanation

## Security Measures

- [ ] Encryption
- [ ] De-identification
- [ ] Access controls
- [ ] Security training
- [ ] Incident response
- [ ] Regular security audits

## Compliance

- [ ] DPO appointed
- [ ] Privacy impact assessment
- [ ] Regular compliance audits
- [ ] Incident reporting to CAC
"""

        with open(docs_dir / "PIPL_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"PIPL compliance checklist generated at {docs_dir / 'PIPL_FULL.md'}"))
