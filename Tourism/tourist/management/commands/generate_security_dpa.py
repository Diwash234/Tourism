"""
Management command to generate DPA compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate DPA compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating DPA compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Data Protection Act Compliance Checklist (UK)

## Data Protection Principles (Section 69)

- [ ] 69(1)(a): Lawfulness, fairness, and transparency
- [ ] 69(1)(b): Purpose limitation
- [ ] 69(1)(c): Data minimization
- [ ] 69(1)(d): Accuracy
- [ ] 69(1)(e): Storage limitation
- [ ] 69(1)(f): Integrity and confidentiality
- [ ] 69(2): Accountability

## Lawful Basis (Section 70)

- [ ] 70(1)(a): Consent
- [ ] 70(1)(b): Contract
- [ ] 70(1)(c): Legal obligation
- [ ] 70(1)(d): Vital interests
- [ ] 70(1)(e): Public task
- [ ] 70(1)(f): Legitimate interests

## Individual Rights (Section 71)

- [ ] 71(1): Right to be informed
- [ ] 71(2): Right of access
- [ ] 71(3): Right to rectification
- [ ] 71(4): Right to erasure
- [ ] 71(5): Right to restrict processing
- [ ] 71(6): Right to data portability
- [ ] 71(7): Right to object
- [ ] 71(8): Rights re: automated decision-making

## Accountability and Governance (Section 72)

- [ ] 72(1): Data protection policy
- [ ] 72(2): DPO appointed
- [ ] 72(3): Records of processing
- [ ] 72(4): DPIA procedures
- [ ] 72(5): Staff training
- [ ] 72(6): Security measures

## International Transfers (Section 73)

- [ ] 73(1): Adequacy regulations
- [ ] 73(2): Appropriate safeguards
- [ ] 73(3): Binding corporate rules
- [ ] 73(4): Derogations

## Children's Data (Section 74)

- [ ] 74(1): Age-appropriate design
- [ ] 74(2): Parental consent
- [ ] 74(3): Best interests of child

## Special Category Data (Section 75)

- [ ] 75(1): Conditions for processing
- [ ] 75(2): Substantial public interest
- [ ] 75(3): Health/social care
- [ ] 75(4): Public health
- [ ] 75(5): Research

## Criminal Offence Data (Section 76)

- [ ] 76(1): Conditions for processing
- [ ] 76(2): Substantial public interest
- [ ] 76(3): Legal claims
- [ ] 76(4): Judicial acts
"""

        with open(docs_dir / "DPA_UK_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"DPA compliance checklist generated at {docs_dir / 'DPA_UK_FULL.md'}"))
