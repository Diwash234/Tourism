"""
Management command to anonymize user data for GDPR compliance.
"""
from django.core.management.base import BaseCommand
from tourist.models import User


class Command(BaseCommand):
    help = "Anonymize user data for GDPR compliance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="Specific user ID to anonymize",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be anonymized without making changes",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        dry_run = options["dry_run"]

        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Anonymize users who haven't logged in for over 2 years
            from datetime import timedelta
            from django.utils import timezone
            cutoff = timezone.now() - timedelta(days=730)
            users = User.objects.filter(last_login__lt=cutoff)

        count = users.count()
        self.stdout.write(f"Found {count} user(s) to anonymize")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made"))
            for user in users:
                self.stdout.write(f"  Would anonymize: {user.email}")
            return

        for user in users:
            # Anonymize personal data
            user.first_name = "Anonymous"
            user.last_name = "User"
            user.email = f"anonymous_{user.id}@deleted.local"
            user.phone_number = ""
            user.save(update_fields=["first_name", "last_name", "email", "phone_number"])
            self.stdout.write(f"  Anonymized: {user.id}")

        self.stdout.write(self.style.SUCCESS(f"Anonymized {count} user(s)"))
