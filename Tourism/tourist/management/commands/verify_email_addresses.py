"""
Management command to verify email addresses in bulk.
"""
from django.core.management.base import BaseCommand
from tourist.models import User


class Command(BaseCommand):
    help = "Verify email addresses in bulk"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="Specific user ID to verify",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Verify all unverified users",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be verified without making changes",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        verify_all = options["all"]
        dry_run = options["dry_run"]

        if user_id:
            users = User.objects.filter(id=user_id)
        elif verify_all:
            users = User.objects.filter(is_verified=False)
        else:
            self.stderr.write("Please specify --user-id or --all")
            return

        count = users.count()
        self.stdout.write(f"Found {count} user(s) to verify")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made"))
            for user in users[:10]:
                self.stdout.write(f"  Would verify: {user.email}")
            return

        for user in users:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            self.stdout.write(f"  Verified: {user.email}")

        self.stdout.write(self.style.SUCCESS(f"Verified {count} user(s)"))
