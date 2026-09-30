"""
Management command to generate a database audit report.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from tourist.models import Destination, User, Review, AuditLog


class Command(BaseCommand):
    help = "Generate a database audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DATABASE AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Table sizes
        self.stdout.write("\nTable Sizes:")
        tables = [
            ("Destinations", Destination),
            ("Users", User),
            ("Reviews", Review),
            ("Audit Logs", AuditLog),
        ]

        for name, model in tables:
            count = model.objects.count()
            self.stdout.write(f"  {name}: {count} records")

        # Orphaned records
        self.stdout.write("\nOrphaned Records:")
        orphaned_reviews = Review.objects.filter(destination__isnull=True).count()
        self.stdout.write(f"  Orphaned reviews: {orphaned_reviews}")

        # Duplicate records
        self.stdout.write("\nDuplicate Records:")
        dup_emails = User.objects.values("email").annotate(
            count=models.Count("id")
        ).filter(count__gt=1)
        self.stdout.write(f"  Duplicate emails: {dup_emails.count()}")

        # Missing data
        self.stdout.write("\nMissing Data:")
        no_category = Destination.objects.filter(category__isnull=True).count()
        no_coords = Destination.objects.filter(
            models.Q(latitude__isnull=True) | models.Q(longitude__isnull=True)
        ).count()
        self.stdout.write(f"  Destinations without category: {no_category}")
        self.stdout.write(f"  Destinations without coordinates: {no_coords}")

        self.stdout.write("\n" + "=" * 60)
