"""
Management command to send bulk notifications to users.
"""
from django.core.management.base import BaseCommand
from tourist.models import User
from tourist.notifications import NotificationService


class Command(BaseCommand):
    help = "Send bulk notifications to users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            type=str,
            required=True,
            help="Notification subject",
        )
        parser.add_argument(
            "--message",
            type=str,
            required=True,
            help="Notification message",
        )
        parser.add_argument(
            "--role",
            type=str,
            help="Send only to users with this role",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without sending",
        )

    def handle(self, *args, **options):
        subject = options["subject"]
        message = options["message"]
        role = options["role"]
        dry_run = options["dry_run"]

        users = User.objects.filter(is_active=True)
        if role:
            users = users.filter(role=role)

        count = users.count()
        self.stdout.write(f"Found {count} users to notify")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no notifications sent"))
            for user in users[:5]:
                self.stdout.write(f"  Would send to: {user.email}")
            return

        service = NotificationService()
        sent = 0
        failed = 0

        for user in users:
            if service.send_email(to_email=user.email, subject=subject, body=message):
                sent += 1
            else:
                failed += 1

        self.stdout.write(self.style.SUCCESS(f"Sent: {sent}, Failed: {failed}"))
