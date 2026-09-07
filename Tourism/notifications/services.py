"""
notifications/services.py

Active email, SMS, push and in-app notification dispatchers.
Re-exported via tourist/utils.py & tourist/notification_delivery.py.
"""
import logging
import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email_notification(to_email, subject, message):
    if not to_email:
        return False
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
        return True
    except Exception as exc:
        logger.error("Email send failed to %s: %s", to_email, exc)
        return False


def send_sms_notification(to_number, message):
    """Sends an SMS via Twilio if credentials are configured; no-op otherwise."""
    if not (getattr(settings, "TWILIO_ACCOUNT_SID", None) and getattr(settings, "TWILIO_AUTH_TOKEN", None) and getattr(settings, "TWILIO_FROM_NUMBER", None)):
        logger.info("SMS not sent (Twilio credentials not configured). Destination %s: %s", to_number, message)
        return False
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=str(to_number))
        return True
    except Exception as exc:
        logger.error("SMS send failed to %s: %s", to_number, exc)
        return False


def send_push_notification(device_tokens, title, message):
    """Sends a push notification via Firebase Cloud Messaging if configured."""
    fcm_key = getattr(settings, "FCM_SERVER_KEY", None)
    if not fcm_key or not device_tokens:
        logger.info("Push skipped (FCM not configured or no tokens). Target count %s: %s", len(device_tokens or []), title)
        return False
    try:
        headers = {
            "Authorization": f"key={fcm_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "registration_ids": device_tokens,
            "notification": {"title": title, "body": message},
        }
        response = requests.post(
            "https://fcm.googleapis.com/fcm/send", json=payload, headers=headers, timeout=5
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Push notification failed: %s", exc)
        return False


def notify_user(user, title, message, channel="in_app", related_alert=None):
    """Creates a Notification record and dispatches it over the requested channel."""
    from tourist.models import Notification

    notification = Notification.objects.create(
        user=user, channel=channel, title=title, message=message
    )

    sent = False
    if channel == "email" and user.email:
        sent = send_email_notification(user.email, title, message)
    elif channel == "sms" and getattr(user, "phone_number", None):
        sent = send_sms_notification(user.phone_number, message)
    elif channel == "push":
        tokens = list(user.device_tokens.values_list("token", flat=True)) if hasattr(user, "device_tokens") else []
        sent = send_push_notification(tokens, title, message)
    else:
        sent = True  # in-app notifications are considered "sent" once stored

    notification.is_sent = sent
    notification.save(update_fields=["is_sent"])
    return notification
