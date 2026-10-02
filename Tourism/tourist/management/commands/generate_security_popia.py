"""
Management command to generate POPIA compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate POPIA compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating POPIA compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# POPIA Compliance Checklist (South Africa)

## Conditions for Lawful Processing

### Accountability (Section 11)
- [ ] Responsible party identified
- [ ] Processing conditions documented

### Processing Limitation (Section 12)
- [ ] Lawful basis established
- [ ] Consent obtained
- [ ] Minimal processing
- [ ] Collection directly from data subject

### Purpose Specification (Section 13)
- [ ] Specific purpose defined
- [ ] Purpose documented
- [ ] Retention period defined

### Further Processing Limitation (Section 14)
- [ ] Compatibility check
- [ ] Consent for further processing

### Information Quality (Section 15)
- [ ] Accurate data
- [ ] Complete data
- [ ] Up-to-date data
- [ ] Correction procedures

### Openness (Section 16)
- [ ] Privacy notice
- [ ] Processing records
- [ ] Notification to data subject

### Security Safeguards (Section 19)
- [ ] Risk assessment
- [ ] Security measures
- [ ] Incident response
- [ ] Regular audits
- [ ] Access controls

### Data Subject Participation (Section 23)
- [ ] Access request process
- [ ] Correction request process
- [ ] Objection process
- [ ] Deletion request process

## Special Personal Information (Section 26)

- [ ] Consent for special PI
- [ ] Prohibition on processing special PI
- [ ] Exceptions documented
- [ ] Children's information protected

## Transborder Flows (Section 72)

- [ ] Adequacy of recipient country
- [ ] Consent for transfer
- [ ] Contractual safeguards
- [ ] Binding corporate rules

## Direct Marketing (Section 69)

- [ ] Consent for direct marketing
- [ ] Opt-out mechanism
- [ ] Suppression list

## Automated Decision-Making (Section 71)

- [ ] Right to object
- [ ] Human intervention
- [ ] Algorithm transparency

## Information Officer (Section 55)

- [ ] Information officer appointed
- [ ] Duties defined
- [ ] Contact published

## Enforcement (Section 74)

- [ ] Complaints procedure
- [ ] Investigation cooperation
- [ ] Enforcement notices
"""

        with open(docs_dir / "POPIA_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"POPIA compliance checklist generated at {docs_dir / 'POPIA_FULL.md'}"))
