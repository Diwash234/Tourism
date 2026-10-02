"""
Management command to generate a business continuity plan.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a business continuity plan"

    def handle(self, *args, **options):
        self.stdout.write("Generating business continuity plan...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Business Continuity Plan

## Critical Functions

1. **User Authentication** - Must remain available
2. **Destination Browsing** - Core functionality
3. **Booking System** - Revenue critical
4. **Emergency Services** - Safety critical

## Recovery Priorities

| Function | RTO | RPO | Priority |
|----------|-----|-----|----------|
| Auth | 1 hour | 0 | P1 |
| Destinations | 2 hours | 1 hour | P1 |
| Bookings | 4 hours | 1 hour | P2 |
| Emergency | 1 hour | 0 | P1 |

## Communication Plan

- Internal: Slack, Email
- External: Status page, Social media
- Customers: Email, In-app notifications
"""

        with open(docs_dir / "BUSINESS_CONTINUITY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Business continuity plan generated at {docs_dir / 'BUSINESS_CONTINUITY.md'}"))
