# """
# notifications/services.py

# send_email_notification, send_sms_notification, send_push_notification,
# and notify_user -- moved from tourist/utils.py. Same logic, unchanged
# behavior. Re-exported from tourist/utils.py (see the README) so every
# existing caller (tourist/views.py's moderation-approval notify, tourist/
# views_auth.py's registration/verification emails, and the `safety` app's
# SOS alert notifications) keeps working with zero changes on their end.
# """
# import logging

# import requests
# from django.conf import settings
# from django.core.mail import send_mail

# logger = logging.getLogger(__name__)


# def send_email_notification(to_email, subject, message):
#     try:
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
#         return True
#     except Exception as exc:  # noqa: BLE001
#         logger.error("Email send failed to %s: %s", to_email, exc)
#         return False


# def send_sms_notification(to_number, message):
#     """Sends an SMS via Twilio if credentials are configured; no-op otherwise."""
#     if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
#         logger.info("SMS not sent (Twilio not configured). Would send to %s: %s", to_number, message)
#         return False
#     try:
#         from twilio.rest import Client

#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=str(to_number))
#         return True
#     except Exception as exc:  # noqa: BLE001
#         logger.error("SMS send failed to %s: %s", to_number, exc)
#         return False


# def send_push_notification(device_tokens, title, message):
#     """Sends a push notification via Firebase Cloud Messaging if configured."""
#     if not settings.FCM_SERVER_KEY or not device_tokens:
#         logger.info("Push not sent (FCM not configured). Would send to %s tokens: %s", len(device_tokens or []), title)
#         return False
#     try:
#         headers = {
#             "Authorization": f"key={settings.FCM_SERVER_KEY}",
#             "Content-Type": "application/json",
#         }
#         payload = {
#             "registration_ids": device_tokens,
#             "notification": {"title": title, "body": message},
#         }
#         response = requests.post(
#             "https://fcm.googleapis.com/fcm/send", json=payload, headers=headers, timeout=5
#         )
#         response.raise_for_status()
#         return True
#     except requests.RequestException as exc:
#         logger.error("Push notification failed: %s", exc)
#         return False


# def notify_user(user, title, message, channel="in_app", related_alert=None):
#     """Creates a Notification record and dispatches it over the requested channel."""
#     from .models import Notification

#     notification = Notification.objects.create(
#         user=user, channel=channel, title=title, message=message, related_alert=related_alert
#     )

#     sent = False
#     if channel == "email":
#         sent = send_email_notification(user.email, title, message)
#     elif channel == "sms" and user.phone_number:
#         sent = send_sms_notification(user.phone_number, message)
#     elif channel == "push":
#         tokens = list(user.device_tokens.values_list("token", flat=True))
#         sent = send_push_notification(tokens, title, message)
#     else:
#         sent = True  # in-app notifications are considered "sent" once stored

#     notification.is_sent = sent
#     notification.save(update_fields=["is_sent"])
#     return notification