"""
Management command to generate PDPA compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate PDPA compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating PDPA compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# PDPA Compliance Checklist (Singapore)

## Consent

- [ ] Consent obtained for collection
- [ ] Consent obtained for use
- [ ] Consent obtained for disclosure
- [ ] Withdrawal of consent process
- [ ] No deemed consent for marketing

## Purpose Limitation

- [ ] Purposes specified
- [ ] Notice of purposes provided
- [ ] No use beyond specified purposes
- [ ] Purpose documented

## Notification

- [ ] Privacy policy published
- [ ] Data collection notice provided
- [ ] Purpose disclosure
- [ ] Retention period stated

## Access and Correction

- [ ] Access request process
- [ ] Correction request process
- [ ] 30-day response time
- [ ] Fee for access requests

## Accuracy

- [ ] Data accuracy measures
- [ ] Regular data review
- [ ] Correction procedures

## Protection

- [ ] Security measures implemented
- [ ] Access controls
- [ ] Encryption
- [ ] Incident response
- [ ] Regular audits

## Retention Limitation

- [ ] Retention policy
- [ ] Data deletion when no longer needed
- [ ] No indefinite retention

## Transfer Limitation

- [ ] Transfer restrictions
- [ ] Adequacy requirements
- [ ] Contractual safeguards

## Data Breach Notification

- [ ] 3-day notification to PDPC
- [ ] Notification to affected individuals
- [ ] Documentation of breaches
- [ ] Risk assessment

## Accountability

- [ ] Data protection officer appointed
- [ ] Policies and procedures documented
- [ ] Staff training
- [ ] DPO contact published

## Do Not Call Registry

- [ ] DNC registry checked
- [ ] Marketing messages compliant
"""

        with open(docs_dir / "PDPA_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"PDPA compliance checklist generated at {docs_dir / 'PDPA_FULL.md'}"))
