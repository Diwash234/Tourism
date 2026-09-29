"""
Notification system — email, SMS, and push notifications with templates.
"""
import logging
from typing import Any, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Unified notification service for email, SMS, and push notifications.

    Usage:
        notification = NotificationService()
        notification.send_email(
            to_email="user@example.com",
            subject="Welcome",
            template="emails/welcome.html",
            context={"name": "John"},
        )
    """

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        template: Optional[str] = None,
        context: Optional[dict] = None,
        body: Optional[str] = None,
    ) -> bool:
        """Send an email notification."""
        try:
            if template and context:
                body = render_to_string(template, context)
            elif not body:
                body = subject

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=body if template else None,
                fail_silently=False,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            return False

    @staticmethod
    def send_sms(phone_number: str, message: str) -> bool:
        """Send an SMS notification via Twilio."""
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("SMS not configured — skipping SMS to %s", phone_number)
            return False

        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_FROM_NUMBER,
                to=phone_number,
            )
            logger.info("SMS sent to %s", phone_number)
            return True
        except Exception as exc:
            logger.error("Failed to send SMS to %s: %s", phone_number, exc)
            return False

    @staticmethod
    def send_push(device_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        """Send a push notification via Firebase Cloud Messaging."""
        if not settings.FCM_SERVER_KEY:
            logger.warning("Push notifications not configured — skipping")
            return False

        try:
            import requests
            headers = {
                "Authorization": f"key={settings.FCM_SERVER_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "to": device_token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Push notification sent to %s", device_token)
            return True
        except Exception as exc:
            logger.error("Failed to send push notification: %s", exc)
            return False

    @staticmethod
    def notify_user(user, subject: str, message: str, notification_type: str = "email") -> bool:
        """Send a notification to a user via their preferred channel."""
        if notification_type == "email" and user.email:
            return NotificationService.send_email(
                to_email=user.email,
                subject=subject,
                body=message,
            )
        elif notification_type == "sms" and hasattr(user, "phone_number") and user.phone_number:
            return NotificationService.send_sms(
                phone_number=str(user.phone_number),
                message=f"{subject}: {message}",
            )
        return False
