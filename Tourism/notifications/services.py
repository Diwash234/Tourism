"""
notifications/services.py -- moved from tourist/utils.py. Same logic.
Re-exported from tourist/utils.py so existing callers there keep
working; the `safety` app imports these directly from here.
"""
import logging

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email_notification(to_email, subject, message):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Email send failed to %s: %s", to_email, exc)
        return False


def send_sms_notification(to_number, message):
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
        logger.info("SMS not sent (Twilio not configured). Would send to %s: %s", to_number, message)
        return False
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=str(to_number))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("SMS send failed to %s: %s", to_number, exc)
        return False


def send_push_notification(device_tokens, title, message):
    fcm_key = getattr(settings, "FCM_SERVER_KEY", "")
    if not fcm_key or not device_tokens:
        logger.info("Push not sent (FCM not configured). Would send to %s tokens: %s", len(device_tokens or []), title)
        return False
    try:
        headers = {"Authorization": f"key={fcm_key}", "Content-Type": "application/json"}
        payload = {"registration_ids": device_tokens, "notification": {"title": title, "body": message}}
        response = requests.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Push notification failed: %s", exc)
        return False


def notify_user(user, title, message, channel="in_app", related_alert=None):
    from .models import Notification

    notification = Notification.objects.create(
        user=user, channel=channel, title=title, message=message, related_alert=related_alert
    )

    sent = False
    if channel == "email":
        sent = send_email_notification(user.email, title, message)
    elif channel == "sms" and user.phone_number:
        sent = send_sms_notification(user.phone_number, message)
    elif channel == "push":
        tokens = list(user.device_tokens.values_list("token", flat=True))
        sent = send_push_notification(tokens, title, message)
    else:
        sent = True

    notification.is_sent = sent
    notification.save(update_fields=["is_sent"])
    return notification