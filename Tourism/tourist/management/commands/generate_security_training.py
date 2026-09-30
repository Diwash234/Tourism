"""
Management command to generate a security training document.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a security training document"

    def handle(self, *args, **options):
        self.stdout.write("Generating security training document...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Training

## For Developers

### Secure Coding Practices
- Input validation
- Output encoding
- Parameterized queries
- Authentication and authorization
- Error handling

### Common Vulnerabilities
- OWASP Top 10
- CWE Top 25
- Security code review checklist

## For Operations

### Incident Detection
- Monitoring alerts
- Log analysis
- Anomaly detection

### Incident Response
- Triage procedures
- Communication plan
- Escalation paths

## For All Employees

### Phishing Awareness
- Recognize phishing attempts
- Report suspicious emails
- Verify requests for sensitive information

### Data Handling
- Classification of data
- Secure storage
- Proper disposal
"""

        with open(docs_dir / "TRAINING.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security training document generated at {docs_dir / 'TRAINING.md'}"))
