"""
Email/SMS Notification Service.

Provides a unified notification service that:
- Sends emails via SMTP or SendGrid
- Sends SMS via Twilio
- Queues notifications for background delivery
- Tracks delivery status
- Supports templates

Usage:
    from tourist.notification_service import NotificationService
    service = NotificationService()
    service.send_email(user.email, "Welcome!", "welcome", {"name": user.first_name})
    service.send_sms(user.phone_number, "Your booking is confirmed!")
"""

import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template import Context, Template
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)

# Email templates
EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "Welcome to Nepal Tourism Portal!",
        "body": "Hi {{ name }},\n\nWelcome to Nepal Tourism Portal! We're excited to have you join our community of travelers.\n\nStart exploring amazing destinations in Nepal today.\n\nBest regards,\nThe Nepal Tourism Portal Team",
    },
    "booking_confirmation": {
        "subject": "Booking Confirmed - {{ booking_reference }}",
        "body": "Hi {{ name }},\n\nYour booking has been confirmed!\n\nBooking Reference: {{ booking_reference }}\nHotel: {{ hotel_name }}\nCheck-in: {{ check_in }}\nCheck-out: {{ check_out }}\n\nWe wish you a wonderful stay!\n\nBest regards,\nThe Nepal Tourism Portal Team",
    },
    "booking_cancellation": {
        "subject": "Booking Cancelled - {{ booking_reference }}",
        "body": "Hi {{ name }},\n\nYour booking has been cancelled.\n\nBooking Reference: {{ booking_reference }}\n\nIf you have any questions, please contact our support team.\n\nBest regards,\nThe Nepal Tourism Portal Team",
    },
    "password_reset": {
        "subject": "Password Reset Request",
        "body": "Hi {{ name }},\n\nWe received a request to reset your password. Use the following code to proceed:\n\n{{ reset_code }}\n\nThis code will expire in 15 minutes.\n\nIf you didn't request this, please ignore this email.\n\nBest regards,\nThe Nepal Tourism Portal Team",
    },
    "review_thanks": {
        "subject": "Thank you for your review!",
        "body": "Hi {{ name }},\n\nThank you for taking the time to review {{ destination_name }}. Your feedback helps other travelers make better decisions.\n\nBest regards,\nThe Nepal Tourism Portal Team",
    },
    "sos_alert": {
        "subject": "SOS Alert - {{ user_name }} needs help",
        "body": "ALERT: {{ user_name }} has triggered an SOS alert.\n\nLocation: {{ location }}\nMessage: {{ message }}\nTime: {{ timestamp }}\n\nPlease respond immediately.",
    },
}

# SMS templates
SMS_TEMPLATES = {
    "booking_confirmation": "Nepal Tourism: Your booking {{ booking_reference }} is confirmed. Check-in: {{ check_in }}. Have a great trip!",
    "sos_alert": "SOS ALERT: {{ user_name }} needs help at {{ location }}. Message: {{ message }}",
    "verification_code": "Your Nepal Tourism Portal verification code is {{ code }}. Valid for 10 minutes.",
    "password_reset": "Your Nepal Tourism Portal password reset code is {{ code }}. Valid for 15 minutes.",
}


class NotificationService:
    """
    Unified notification service for email and SMS delivery.

    Supports:
    - SMTP (Django's built-in email backend)
    - SendGrid (via API)
    - Twilio (for SMS)
    - In-app notifications (via Notification model)
    """

    def __init__(self):
        self.use_sendgrid = bool(getattr(settings, "SENDGRID_API_KEY", ""))
        self.sendgrid_api_key = getattr(settings, "SENDGRID_API_KEY", "")
        self.twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.twilio_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.twilio_from = getattr(settings, "TWILIO_FROM_NUMBER", "")

    # ------------------------------------------------------------------
    # Email Sending
    # ------------------------------------------------------------------

    def send_email(self, to_email, subject, template_name=None, context=None, body=None):
        """
        Send an email to a recipient.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            template_name: Name of the template to use (from EMAIL_TEMPLATES).
            context: Dict of template variables.
            body: Raw email body (used if template_name is None).

        Returns:
            True if sent successfully, False otherwise.
        """
        context = context or {}

        if template_name and template_name in EMAIL_TEMPLATES:
            template = EMAIL_TEMPLATES[template_name]
            subject = self._render_template(template["subject"], context)
            body = self._render_template(template["body"], context)

        if not body:
            logger.error(f"No email body for template: {template_name}")
            return False

        try:
            if self.use_sendgrid:
                return self._send_email_sendgrid(to_email, subject, body)
            else:
                return self._send_email_smtp(to_email, subject, body)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _send_email_smtp(self, to_email, subject, body):
        """Send email via Django's SMTP backend."""
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return True

    def _send_email_sendgrid(self, to_email, subject, body):
        """Send email via SendGrid API."""
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": settings.DEFAULT_FROM_EMAIL},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }

        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return True

    # ------------------------------------------------------------------
    # SMS Sending
    # ------------------------------------------------------------------

    def send_sms(self, to_number, message, template_name=None, context=None):
        """
        Send an SMS to a recipient.

        Args:
            to_number: Recipient phone number (E.164 format recommended).
            message: SMS message body (used if template_name is None).
            template_name: Name of the SMS template (from SMS_TEMPLATES).
            context: Dict of template variables.

        Returns:
            True if sent successfully, False otherwise.
        """
        context = context or {}

        if template_name and template_name in SMS_TEMPLATES:
            message = self._render_template(SMS_TEMPLATES[template_name], context)

        if not message:
            logger.error(f"No SMS message for template: {template_name}")
            return False

        if not self.twilio_sid or not self.twilio_token or not self.twilio_from:
            logger.warning("Twilio is not configured, SMS not sent")
            return False

        try:
            return self._send_sms_twilio(to_number, message)
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False

    def _send_sms_twilio(self, to_number, message):
        """Send SMS via Twilio API."""
        from twilio.rest import Client

        client = Client(self.twilio_sid, self.twilio_token)
        client.messages.create(
            body=message[:1600],
            from_=self.twilio_from,
            to=to_number,
        )
        return True

    # ------------------------------------------------------------------
    # In-App Notifications
    # ------------------------------------------------------------------

    def send_in_app(self, user, title, message, category="general", metadata=None):
        """
        Send an in-app notification (stored in the database).

        Args:
            user: The User to notify.
            title: Notification title.
            message: Notification message.
            category: Notification category.
            metadata: Optional dict of additional data.

        Returns:
            The created Notification instance.
        """
        notification = Notification.objects.create(
            user=user,
            title=title[:200],
            message=message,
            channel=Notification.Channel.IN_APP,
            category=category,
            metadata=metadata or {},
            is_sent=True,
            delivery_status=Notification.DeliveryStatus.SENT,
            sent_at=timezone.now(),
        )
        return notification

    # ------------------------------------------------------------------
    # Queued Notifications
    # ------------------------------------------------------------------

    def queue_notification(self, user, title, message, channel="email", category="general", template_name=None, context=None):
        """
        Queue a notification for background delivery.

        Args:
            user: The User to notify.
            title: Notification title.
            message: Notification message.
            channel: Delivery channel ("email", "sms", "in_app", "push").
            category: Notification category.
            template_name: Optional template to use.
            context: Template context dict.

        Returns:
            The created Notification instance.
        """
        notification = Notification.objects.create(
            user=user,
            title=title[:200],
            message=message,
            channel=channel,
            category=category,
            delivery_status=Notification.DeliveryStatus.QUEUED,
        )

        # If a template is provided, render it
        if template_name:
            if channel == "email" and template_name in EMAIL_TEMPLATES:
                template = EMAIL_TEMPLATES[template_name]
                notification.title = self._render_template(template["subject"], context or {})
                notification.message = self._render_template(template["body"], context or {})
            elif channel == "sms" and template_name in SMS_TEMPLATES:
                notification.message = self._render_template(SMS_TEMPLATES[template_name], context or {})
            notification.save()

        return notification

    def process_queue(self, batch_size=50):
        """
        Process queued notifications.

        Args:
            batch_size: Maximum number of notifications to process.

        Returns:
            dict with counts of sent/failed notifications.
        """
        queued = Notification.objects.filter(
            delivery_status=Notification.DeliveryStatus.QUEUED,
        ).select_related("user")[:batch_size]

        results = {"sent": 0, "failed": 0}

        for notification in queued:
            try:
                if notification.channel == Notification.Channel.EMAIL:
                    success = self.send_email(
                        notification.user.email,
                        notification.title,
                        body=notification.message,
                    )
                elif notification.channel == Notification.Channel.SMS:
                    success = self.send_sms(
                        str(notification.user.phone_number),
                        notification.message,
                    )
                elif notification.channel == Notification.Channel.PUSH:
                    success = self._send_push(notification)
                else:
                    success = True  # In-app is already "sent"

                if success:
                    notification.delivery_status = Notification.DeliveryStatus.SENT
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    results["sent"] += 1
                else:
                    notification.delivery_status = Notification.DeliveryStatus.FAILED
                    notification.failure_reason = "Delivery failed"
                    results["failed"] += 1

            except Exception as e:
                notification.delivery_status = Notification.DeliveryStatus.FAILED
                notification.failure_reason = str(e)[:500]
                results["failed"] += 1

            notification.delivery_attempts += 1
            notification.last_attempt_at = timezone.now()
            notification.save()

        return results

    def _send_push(self, notification):
        """Send a push notification via FCM."""
        from .models import DeviceToken

        tokens = list(DeviceToken.objects.filter(user=notification.user).values_list("token", flat=True))
        if not tokens:
            return False

        fcm_key = getattr(settings, "FCM_SERVER_KEY", "")
        if not fcm_key:
            return False

        response = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            json={
                "registration_ids": tokens,
                "notification": {
                    "title": notification.title,
                    "body": notification.message,
                },
            },
            headers={
                "Authorization": f"key={fcm_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        return True

    # ------------------------------------------------------------------
    # Template Rendering
    # ------------------------------------------------------------------

    @staticmethod
    def _render_template(template_str, context):
        """Render a template string with the given context."""
        template = Template(template_str)
        return template.render(Context(context))

    # ------------------------------------------------------------------
    # Delivery Status
    # ------------------------------------------------------------------

    def get_delivery_status(self, notification_id):
        """
        Get the delivery status of a notification.

        Returns:
            dict with status information.
        """
        try:
            notification = Notification.objects.get(id=notification_id)
            return {
                "id": notification.id,
                "status": notification.delivery_status,
                "channel": notification.channel,
                "attempts": notification.delivery_attempts,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "failure_reason": notification.failure_reason,
            }
        except Notification.DoesNotExist:
            return {"error": "Notification not found"}

    def get_user_notifications(self, user, unread_only=False, limit=50):
        """
        Get notifications for a user.

        Args:
            user: The User to get notifications for.
            unread_only: If True, return only unread notifications.
            limit: Maximum number to return.

        Returns:
            QuerySet of Notification instances.
        """
        qs = Notification.objects.filter(user=user)
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs.order_by("-created_at")[:limit]
