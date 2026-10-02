"""
Management command to generate CCPA/CPRA compliance checklist.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate CCPA/CPRA compliance checklist"

    def handle(self, *args, **options):
        self.stdout.write("Generating CCPA/CPRA compliance checklist...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# CCPA/CPRA Compliance Checklist

## Consumer Rights

### Right to Know
- [ ] Categories of PI collected
- [ ] Purposes for collection
- [ ] Categories of third parties
- [ ] Specific pieces of PI
- [ ] Right to know request process
- [ ] 45-day response time

### Right to Delete
- [ ] Deletion request process
- [ ] Verification of requester
- [ ] Exceptions documented
- [ ] Service provider notification

### Right to Opt-Out
- [ ] "Do Not Sell or Share" link
- [ ] Opt-out request process
- [ ] 12-month waiting period
- [ ] GPC signal honored

### Right to Correct
- [ ] Correction request process
- [ ] Verification of requester

### Right to Non-Discrimination
- [ ] No discrimination for exercising rights
- [ ] No different pricing
- [ ] No different service quality

## Business Obligations

### Notice at Collection
- [ ] Privacy policy updated
- [ ] Data collection notice provided
- [ ] Purpose disclosure
- [ ] Third party disclosure

### Service Provider Contracts
- [ ] Contracts with service providers
- [ ] Prohibition on selling/sharing PI
- [ ] Certification of understanding
- [ ] Right to monitor

### Risk Assessments
- [ ] Risk assessments conducted
- [ ] High-risk processing identified

### Cybersecurity Audits
- [ ] Regular cybersecurity audits

### Training
- [ ] Staff training on CCPA/CPRA
- [ ] Request handling procedures

## Sensitive Personal Information

- [ ] SSN protected
- [ ] Driver's license protected
- [ ] Financial account protected
- [ ] Precise geolocation protected
- [ ] Racial/ethnic origin protected
- [ ] Religious beliefs protected
- [ ] Union membership protected
- [ ] Genetic data protected
- [ ] Biometric data protected
- [ ] Health data protected
- [ ] Sex life/orientation protected

## Data Broker Registration

- [ ] Registered as data broker (if applicable)
- [ ] Annual registration completed

## Enforcement

- [ ] 30-day cure period process
- [ ] Penalties documented
"""

        with open(docs_dir / "CCPA_CPRA.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"CCPA/CPRA compliance checklist generated at {docs_dir / 'CCPA_CPRA.md'}"))
