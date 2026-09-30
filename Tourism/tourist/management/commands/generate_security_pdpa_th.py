"""
Management command to generate PDPA Thailand compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate PDPA Thailand compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating PDPA Thailand compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# PDPA Compliance Checklist (Thailand)

## Consent

- [ ] Explicit consent obtained
- [ ] Written consent for sensitive data
- [ ] Consent withdrawal mechanism
- [ ] Parental consent for minors
- [ ] No pre-ticked consent boxes

## Notice

- [ ] Purpose of collection
- [ ] Data retention period
- [ ] Rights of data subjects
- [ ] Contact information
- [ ] Third party disclosure

## Data Subject Rights

- [ ] Right to access
- [ ] Right to data portability
- [ ] Right to object
- [ ] Right to erasure
- [ ] Right to restrict processing
- [ ] Right to rectification
- [ ] Right to withdraw consent

## Security

- [ ] Appropriate security measures
- [ ] Access controls
- [ ] Encryption
- [ ] Incident response
- [ ] Regular audits
- [ ] Staff training

## Data Breach

- [ ] 72-hour notification
- [ ] Authority notification
- [ ] Data subject notification
- [ ] Documentation
- [ ] Risk assessment

## Cross-Border Transfer

- [ ] Adequacy decision
- [ ] Appropriate safeguards
- [ ] Consent for transfer
- [ ] Contractual clauses

## Sensitive Data

- [ ] Consent for sensitive data
- [ ] Racial/ethnic origin protected
- [ ] Political opinions protected
- [ ] Religious beliefs protected
- [ ] Health data protected
- [ ] Biometric data protected
- [ ] Genetic data protected

## DPO

- [ ] DPO appointed
- [ ] DPO contact published
- [ ] DPO responsibilities defined

## PDPC Registration

- [ ] Registered with PDPC
- [ ] Annual registration completed
"""

        with open(docs_dir / "PDPA_TH_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"PDPA Thailand compliance checklist generated at {docs_dir / 'PDPA_TH_FULL.md'}"))
