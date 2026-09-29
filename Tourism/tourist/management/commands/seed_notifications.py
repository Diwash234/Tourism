"""
Management command to seed notification templates.
"""
from django.core.management.base import BaseCommand
from tourist.models import NotificationTemplate


class Command(BaseCommand):
    help = "Seed default notification templates"

    def handle(self, *args, **options):
        templates = [
            {
                "name": "welcome",
                "subject": "Welcome to Nepal Tourism Platform",
                "body": "Welcome {name}! Your account has been created successfully.",
                "notification_type": "email",
            },
            {
                "name": "verification",
                "subject": "Verify your email address",
                "body": "Please verify your email by clicking the link: {link}",
                "notification_type": "email",
            },
            {
                "name": "password_reset",
                "subject": "Password reset request",
                "body": "Click the link to reset your password: {link}",
                "notification_type": "email",
            },
            {
                "name": "booking_confirmation",
                "subject": "Booking confirmed",
                "body": "Your booking for {destination} has been confirmed.",
                "notification_type": "email",
            },
            {
                "name": "sos_alert",
                "subject": "SOS Alert",
                "body": "SOS alert triggered by {name} at {location}",
                "notification_type": "sms",
            },
        ]

        for template in templates:
            NotificationTemplate.objects.get_or_create(
                name=template["name"],
                defaults=template,
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(templates)} notification templates"))
