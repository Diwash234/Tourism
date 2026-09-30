"""
Management command to generate a runbook.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a runbook"

    def handle(self, *args, **options):
        self.stdout.write("Generating runbook...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Runbook

## Common Issues

### Database Connection Failed
1. Check DATABASE_URL environment variable
2. Verify database server is running
3. Check network connectivity
4. Review database logs

### High Response Time
1. Check server load
2. Review slow query log
3. Check cache hit rate
4. Scale horizontally if needed

### High Error Rate
1. Check error logs
2. Identify common error patterns
3. Roll back recent deployments if needed
4. Notify on-call engineer

## Emergency Procedures

### Database Failover
1. Promote replica to primary
2. Update DATABASE_URL
3. Verify application connectivity
4. Notify stakeholders

### Cache Flush
1. Identify affected keys
2. Warm cache with critical data
3. Monitor cache hit rate
4. Investigate root cause

### Security Incident
1. Isolate affected systems
2. Preserve evidence
3. Notify security team
4. Follow incident response plan
"""

        with open(docs_dir / "RUNBOOK.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Runbook generated at {docs_dir / 'RUNBOOK.md'}"))
