"""
Management command to generate security advisories template.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security advisories template"

    def handle(self, *args, **options):
        self.stdout.write("Generating security advisories template...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Advisories

## [YEAR-001] [VULNERITY TITLE]

**Date:** YYYY-MM-DD
**Severity:** Critical/High/Medium/Low
**Affected Versions:** < 1.0.0
**Fixed Version:** 1.0.1

### Description

Brief description of the vulnerability.

### Impact

What could happen if exploited.

### Mitigation

How to fix or mitigate.

### References

- [CVE-XXXX-XXXXX](https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX)
"""

        with open(docs_dir / "TEMPLATE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security advisories template generated at {docs_dir / 'TEMPLATE.md'}"))
