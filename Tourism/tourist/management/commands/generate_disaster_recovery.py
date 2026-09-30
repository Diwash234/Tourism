"""
Management command to generate a disaster recovery plan.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a disaster recovery plan"

    def handle(self, *args, **options):
        self.stdout.write("Generating disaster recovery plan...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Disaster Recovery Plan

## Recovery Objectives

- **RPO** (Recovery Point Objective): 1 hour
- **RTO** (Recovery Time Objective): 4 hours

## Backup Strategy

### Database
- Full backup: Daily at 2 AM UTC
- Incremental backup: Every 4 hours
- Retention: 30 days

### Files
- Media files: Daily sync to S3
- Static files: On-demand rebuild

## Recovery Procedures

### Database Recovery
1. Provision new database instance
2. Restore from latest backup
3. Apply incremental backups
4. Verify data integrity
5. Update connection strings

### Application Recovery
1. Deploy new container
2. Run migrations
3. Verify health checks
4. Update DNS/load balancer

## Testing
- Quarterly DR drills
- Automated backup verification
- Recovery time measurement
"""

        with open(docs_dir / "DISASTER_RECOVERY.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Disaster recovery plan generated at {docs_dir / 'DISASTER_RECOVERY.md'}"))
