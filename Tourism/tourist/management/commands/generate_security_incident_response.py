"""
Management command to generate security incident response procedures.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate security incident response procedures"

    def handle(self, *args, **options):
        self.stdout.write("Generating security incident response procedures...")

        docs_dir = Path("docs/security")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Security Incident Response

## Phase 1: Preparation
- Incident response team assigned
- Communication channels established
- Tools and access ready

## Phase 2: Identification
- Detect and classify the incident
- Assess scope and impact
- Document initial findings

## Phase 3: Containment
- Short-term containment
- Long-term containment
- Evidence preservation

## Phase 4: Eradication
- Remove threat
- Patch vulnerabilities
- Harden systems

## Phase 5: Recovery
- Restore systems
- Monitor for recurrence
- Validate integrity

## Phase 6: Lessons Learned
- Post-incident review
- Update procedures
- Share knowledge
"""

        with open(docs_dir / "INCIDENT_RESPONSE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Security incident response procedures generated at {docs_dir / 'INCIDENT_RESPONSE.md'}"))
