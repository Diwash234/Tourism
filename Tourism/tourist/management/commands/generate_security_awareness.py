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
- Smishing (SMS phishing)
- Vishing (voice phishing)

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
- Shoulder surfing
- Device theft
- Dumpster diving

## Best Practices

### Email Security
- Verify sender
- Check links
- Don't open attachments
- Report suspicious emails

### Web Security
- Check for HTTPS
- Be cautious with downloads
- Use strong passwords
- Enable MFA

### Mobile Security
- Keep devices updated
- Use strong PINs
- Enable remote wipe
- Be cautious with public Wi-Fi

### Social Media
- Limit personal information
- Check privacy settings
- Be cautious with friend requests
- Think before posting

## Incident Response

### What to Do
- Report immediately
- Don't delete evidence
- Cooperate with investigation
- Learn from the incident

### Who to Contact
- IT Security: security@example.com
- Manager: [Manager Name]
- HR: [HR Contact]
- Legal: [Legal Contact]
"""

        with open(docs_dir / "AWARENESS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security awareness materials generated at {docs_dir / 'AWARENESS.md'}"))
