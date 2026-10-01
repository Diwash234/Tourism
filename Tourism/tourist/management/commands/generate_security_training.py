"""
Management command to generate security training materials.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security training materials"

    def handle(self, *args, **options):
        self.stdout.write("Generating security training materials...")

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
- Report data breaches immediately

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

### Authentication
- Implement MFA
- Secure session management
- Password hashing
- Account lockout

### Authorization
- Principle of least privilege
- Role-based access control
- Object-level permissions
- Regular access reviews

### Data Protection
- Encryption at rest
- Encryption in transit
- Data minimization
- Secure backups

## For Administrators

### System Security
- Regular patching
- Configuration management
- Monitoring and alerting
- Incident response

### Network Security
- Firewall configuration
- Network segmentation
- VPN access
- DDoS protection

### Access Control
- User provisioning
- Access reviews
- Privileged access management
- Audit logging

### Compliance
- Policy enforcement
- Audit preparation
- Reporting
- Continuous improvement
"""

        with open(docs_dir / "TRAINING.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security training materials generated at {docs_dir / 'TRAINING.md'}"))
