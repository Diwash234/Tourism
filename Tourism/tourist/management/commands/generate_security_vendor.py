"""
Management command to generate security vendor assessment.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security vendor assessment"

    def handle(self, *args, **options):
        self.stdout.write("Generating security vendor assessment...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Vendor Assessment

## Evaluation Criteria

| Criteria | Weight | Score |
|----------|--------|-------|
| Security features | 30% | - |
| Compliance certifications | 20% | - |
| Support quality | 15% | - |
| Cost | 15% | - |
| Integration ease | 10% | - |
| Reputation | 10% | - |

## Vendors

### [Vendor Name]
- Features: [list]
- Certifications: [list]
- Pricing: [details]
- Pros: [list]
- Cons: [list]
- Recommendation: [yes/no]
"""

        with open(docs_dir / "VENDOR_ASSESSMENT.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security vendor assessment generated at {docs_dir / 'VENDOR_ASSESSMENT.md'}"))
