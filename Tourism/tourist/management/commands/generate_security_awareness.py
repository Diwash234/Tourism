"""
Management command to generate security awareness materials.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security awareness materials"

    def handle(self, *args, **options):
        self.stdout.write("Generating security awareness materials...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Awareness

## Common Threats

### Phishing
- Spear phishing
- Whaling
- Smishing
- Vishing

### Malware
- Ransomware
- Trojans
- Spyware
- Keyloggers

### Social Engineering
- Pretexting
- Baiting
- Tailgating
- Quid pro quo

### Physical Threats
- Tailgating
- Dumpster diving
- Shoulder surfing
- Device theft

## Best Practices

### Email Security
- Verify sender
- Check links
- Don't open attachments
- Report suspicious emails

### Web Security
- Check for HTTPS
- Avoid public Wi-Fi
- Use a VPN
- Keep browsers updated

### Mobile Security
- Use strong PINs
- Enable remote wipe
- Install updates
- Be cautious with apps

### Social Media
- Limit personal information
- Check privacy settings
- Be cautious with friend requests
- Think before posting

## Incident Reporting

### What to Report
- Suspicious emails
- Unauthorized access
- Data breaches
- Lost devices
- Security vulnerabilities

### How to Report
- Email: security@example.com
- Phone: +1-555-0123
- Online: https://example.com/report
- In person: Security office

### After Reporting
- Preserve evidence
- Don't investigate yourself
- Cooperate with investigation
- Learn from the incident
"""

        with open(docs_dir / "AWARENESS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security awareness materials generated at {docs_dir / 'AWARENESS.md'}"))
