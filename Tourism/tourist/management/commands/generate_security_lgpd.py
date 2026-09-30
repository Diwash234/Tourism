"""
Management command to generate LGPD compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate LGPD compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating LGPD compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# LGPD Compliance Checklist (Brazil)

## Legal Bases (Article 7)

- [ ] I - Consent
- [ ] II - Legal obligation
- [ ] III - Public policy
- [ ] IV - Research
- [ ] V - Contract execution
- [ ] VI - Regular exercise of rights
- [ ] VII - Credit protection
- [ ] VIII - Health protection
- [ ] IX - Legitimate interest
- [ ] X - Vital interest protection

## Data Subject Rights (Article 18)

- [ ] I - Confirmation of processing
- [ ] II - Access to data
- [ ] III - Correction of data
- [ ] IV - Anonymization/blocking
- [ ] V - Portability
- [ ] VI - Deletion
- [ ] VII - Information about sharing
- [ ] VIII - Information about consent
- [ ] IX - Revocation of consent

## DPO (Article 41)

- [ ] DPO appointed
- [ ] DPO contact published
- [ ] DPO responsibilities defined

## Security (Article 46)

- [ ] Security standards
- [ ] Access controls
- [ ] Encryption
- [ ] Incident response
- [ ] Regular audits

## International Transfers (Article 33)

- [ ] Adequacy decision
- [ ] Specific consent
- [ ] Contractual clauses
- [ ] Other legal bases

## Data Breach (Article 48)

- [ ] ANPD notification
- [ ] Data subject notification
- [ ] Documentation

## Consent Management

- [ ] Clear consent request
- [ ] Granular consent options
- [ ] Consent withdrawal mechanism
- [ ] Consent records maintained

## Children's Data (Article 14)

- [ ] Best interest of child
- [ ] Verifiable parental consent
- [ ] Minimal data collection
"""

        with open(docs_dir / "LGPD_FULL.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"LGPD compliance checklist generated at {docs_dir / 'LGPD_FULL.md'}"))
