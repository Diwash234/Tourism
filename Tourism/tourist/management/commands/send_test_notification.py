"""
Management command to send a test notification.
"""
from django.core.management.base import BaseCommand
from tourist.notifications import NotificationService


class Command(BaseCommand):
    help = "Send a test notification to verify the notification system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address to send test to",
        )
        parser.add_argument(
            "--type",
            type=str,
            choices=["email", "sms", "push"],
            default="email",
            help="Notification type",
        )

    def handle(self, *args, **options):
        email = options["email"]
        notification_type = options["type"]

        self.stdout.write(f"Sending test {notification_type} notification to {email}...")

        service = NotificationService()

        if notification_type == "email":
            success = service.send_email(
                to_email=email,
                subject="Test Notification from Nepal Tourism Platform",
                body="This is a test email. If you received this, your email configuration is working correctly.",
            )
        elif notification_type == "sms":
            success = service.send_sms(
                phone_number=email,
                message="Test SMS from Nepal Tourism Platform",
            )
        else:
            self.stderr.write("Push notifications require a device token")
            return

        if success:
            self.stdout.write(self.style.SUCCESS("Test notification sent successfully"))
        else:
            self.stderr.write("Failed to send test notification")
