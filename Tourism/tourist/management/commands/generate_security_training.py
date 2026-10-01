"""
Management command to generate security training document.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security training document"

    def handle(self, *args, **options):
        self.stdout.write("Generating security training document...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Training

## For All Employees

### Password Security
- Use strong, unique passwords
- Enable MFA
- Never share passwords
- Use a password manager

### Phishing Awareness
- Verify sender email addresses
- Hover over links before clicking
- Report suspicious emails
- Never open unexpected attachments

### Data Handling
- Classify data appropriately
- Encrypt sensitive data
- Follow retention policies
- Secure physical documents

### Physical Security
- Lock your desk
- Use privacy screens
- Secure mobile devices
- Report unauthorized access

## For Developers

### Secure Coding
- Input validation
- Output encoding
- Parameterized queries
- Error handling

### Common Vulnerabilities
- OWASP Top 10
- CWE Top 25
- Security code reviews
- Automated testing

### Authentication & Authorization
- Implement MFA
- Use RBAC
- Secure session management
- Regular access reviews

## For Administrators

### System Security
- Regular patching
- Configuration management
- Monitoring and alerting
- Incident response

### Access Control
- Principle of least privilege
- Regular access reviews
- Privileged access management
- Audit logging
"""

        with open(docs_dir / "TRAINING.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security training document generated at {docs_dir / 'TRAINING.md'}"))
