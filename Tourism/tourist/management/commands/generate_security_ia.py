"""
Management command to generate privacy impact assessment.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate privacy impact assessment"

    def handle(self, *args, **options):
        self.stdout.write("Generating privacy impact assessment...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Privacy Impact Assessment

## Project Information

- Project name: [Name]
- Date: [Date]
- Assessor: [Name]
- Version: [Version]

## Data Flows

| Source | Data | Destination | Purpose |
|--------|------|-------------|---------|
| User | Email | Database | Authentication |
| User | Location | ML Service | Recommendations |
| User | Preferences | Database | Personalization |

## Privacy Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Unauthorized access | Low | High | Access controls |
| Data breach | Low | High | Encryption |
| Function creep | Medium | High | Purpose limitation |
| Third-party sharing | Medium | Medium | Contracts |
| Retention violation | Low | Medium | Retention policy |

## Compliance

- [ ] Lawful basis identified
- [ ] DPIA required: [yes/no]
- [ ] Consultation needed: [yes/no]
- [ ] Prior authorization: [yes/no]

## Recommendations

1. Implement privacy by design
2. Conduct regular audits
3. Provide privacy training
4. Establish data retention policy
5. Implement data minimization

## Sign-off

- Assessor: _________________ Date: _________
- DPO: _________________ Date: _________
- Project Manager: _________________ Date: _________
"""

        with open(docs_dir / "PIA_ASSESSMENT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Privacy impact assessment generated at {docs_dir / 'PIA_ASSESSMENT.md'}"))
