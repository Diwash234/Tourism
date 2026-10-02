"""
Management command to generate API usage metrics report.
"""
import json
from collections import Counter
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
        parser.add_argument(
            "--output",
            type=str,
            default="api_metrics.json",
            help="Output file path",
        )

    def handle(self, *args, **options):
        days = options["days"]
        output = options["output"]
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write(f"Generating API metrics for last {days} days...")

        # Total requests
        total = AuditLog.objects.filter(created_at__gte=cutoff).count()
        self.stdout.write(f"\nTotal API requests: {total}")

        # Requests by method
        self.stdout.write("\nRequests by HTTP method:")
        methods = AuditLog.objects.filter(
            created_at__gte=cutoff
        ).values("method").annotate(count=Counter("id")).order_by("-count")
        for m in methods:
            self.stdout.write(f"  {m['method']}: {m['count']}")

        # Requests by status code
        self.stdout.write("\nRequests by status code:")
        statuses = AuditLog.objects.filter(
            created_at__gte=cutoff
        ).values("status_code").annotate(count=Counter("id")).order_by("-status_code")
        for s in statuses:
            self.stdout.write(f"  {s['status_code']}: {s['count']}")

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
        ).values("endpoint").annotate(count=Counter("id")).order_by("-count")[:10]
        for e in endpoints:
            self.stdout.write(f"  {e['endpoint']}: {e['count']}")

        # Save to file
        metrics = {
            "period_days": days,
            "total_requests": total,
            "error_rate": round(error_rate, 2),
            "by_method": {m["method"]: m["count"] for m in methods},
            "by_status": {s["status_code"]: s["count"] for s in statuses},
            "top_endpoints": {e["endpoint"]: e["count"] for e in endpoints},
        }
        with open(output, "w") as f:
            json.dump(metrics, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"\nMetrics saved to {output}"))
