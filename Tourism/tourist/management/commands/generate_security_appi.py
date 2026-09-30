"""
Management command to generate APPI compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate APPI compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating APPI compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# APPI Compliance Checklist (Japan)

## Purpose Specification

- [ ] Purpose of use specified
- [ ] Notice of purpose
- [ ] No use beyond purpose without consent
- [ ] Purpose documented

## Proper Acquisition

- [ ] Lawful and fair means
- [ ] Consent obtained when required
- [ ] No misleading representations
- [ ] No acquisition from third parties without consent

## Notification

- [ ] Privacy policy published
- [ ] Purpose of use disclosed
- [ ] Retention period stated
- [ ] Third party provision disclosed

## Security

- [ ] Access control
- [ ] Leak prevention
- [ ] Loss prevention
- [ ] Damage recovery
- [ ] External storage management

## Third-Party Provision

- [ ] Consent obtained for provision
- [ ] Records of provision maintained
- [ ] Supervision of recipients
- [ ] Provision records kept

## Anonymization

- [ ] Anonymization standards met
- [ ] Re-identification prevention
- [ ] Disclosure restrictions
- [ ] Processing restrictions

## Data Subject Rights

- [ ] Disclosure request process
- [ ] Correction request process
- [ ] Suspension request process
- [ ] Deletion request process
- [ ] Opt-out process

## Special Care-Required Personal Information

- [ ] Consent required for special care PI
- [ ] Racial/ethnic origin protected
- [ ] Medical history protected
- [ ] Criminal history protected
- [ ] Social status protected

## PPC Reporting

- [ ] Breach notification to PPC
- [ ] Annual report to PPC
"""

        with open(docs_dir / "APPI_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"APPI compliance checklist generated at {docs_dir / 'APPI_FULL.md'}"))
