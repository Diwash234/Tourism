"""
Management command to generate API usage metrics report.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import AuditLog


class Command(BaseCommand):
    help = "Generate API usage metrics report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to report on (default: 30)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write("=" * 60)
        self.stdout.write(f"API USAGE METRICS REPORT (last {days} days)")
        self.stdout.write("=" * 60)

        # Total requests
        total = AuditLog.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"\nTotal API requests: {total}")

        # Requests by method
        self.stdout.write("\nRequests by HTTP method:")
        methods = AuditLog.objects.filter(
            created_at__gte=cutoff
        ).values("method").annotate(count=models.Count("id")).order_by("-count")
        for m in methods:
            self.stdout.write(f"  {m['method']}: {m['count']}")

        # Requests by status code
        self.stdout.write("\nRequests by status code:")
        statuses = AuditLog.objects.filter(
            created_at__gte=cutoff
        ).values("status_code").annotate(count=models.Count("id")).order_by("-status_code")
        for s in statuses:
            self.stdout.write(f"  {s['status_code']}: {s['count']}")

        # Error rate
        errors = AuditLog.objects.filter(
            created_at__gte=cutoff,
            severity__in=["error", "warning"],
        ).count()
        error_rate = (errors / total * 100) if total > 0 else 0
        self.stdout.write(f"\nError rate: {error_rate:.1f}%")

        # Average response time
        self.stdout.write("\nResponse time metrics:")
        slow_requests = AuditLog.objects.filter(
            created_at__gte=cutoff,
            extra__duration_ms__gt=2000,
        ).count()
        self.stdout.write(f"  Slow requests (>2s): {slow_requests}")

        self.stdout.write("\n" + "=" * 60)
