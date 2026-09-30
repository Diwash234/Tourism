"""
Management command to generate an API usage report.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tourist.models import AuditLog


class Command(BaseCommand):
    help = "Generate an API usage report"

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
        self.stdout.write(f"API USAGE REPORT (last {days} days)")
        self.stdout.write("=" * 60)

        # Total requests
        total = AuditLog.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"\nTotal API requests: {total}")

        # Requests by category
        self.stdout.write("\nRequests by category:")
        categories = AuditLog.objects.filter(
            created_at__gte=cutoff
        ).values("category").annotate(count=models.Count("id")).order_by("-count")
        for cat in categories:
            self.stdout.write(f"  {cat['category']}: {cat['count']}")

        # Error rate
        errors = AuditLog.objects.filter(
            created_at__gte=cutoff,
            severity__in=["error", "warning"],
        ).count()
        error_rate = (errors / total * 100) if total > 0 else 0
        self.stdout.write(f"\nError rate: {error_rate:.1f}%")

        # Most active endpoints
        self.stdout.write("\nMost active endpoints:")
        endpoints = AuditLog.objects.filter(
            created_at__gte=cutoff
        ).values("endpoint").annotate(count=models.Count("id")).order_by("-count")[:10]
        for ep in endpoints:
            self.stdout.write(f"  {ep['endpoint']}: {ep['count']} requests")

        self.stdout.write("\n" + "=" * 60)
