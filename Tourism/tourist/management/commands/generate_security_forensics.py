"""
Management command to generate digital forensics procedures.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate digital forensics procedures"

    def handle(self, *args, **options):
        self.stdout.write("Generating digital forensics procedures...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Digital Forensics Procedures

## Evidence Collection

1. **Preserve** - Create forensic images
2. **Document** - Record chain of custody
3. **Analyze** - Examine evidence
4. **Report** - Document findings

## Tools

- FTK Imager
- Autopsy
- Wireshark
- Volatility

## Procedures

### Disk Imaging
1. Write-block the source drive
2. Create bit-for-bit copy
3. Verify hash integrity
4. Store securely

### Log Analysis
1. Collect relevant logs
2. Establish timeline
3. Identify anomalies
4. Correlate events
"""

        with open(docs_dir / "FORENSICS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Digital forensics procedures generated at {docs_dir / 'FORENSICS.md'}"))
