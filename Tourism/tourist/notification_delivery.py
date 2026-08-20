"""Provider-backed notification delivery with honest status and bounded retries."""
from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone

from .models import DeviceToken, Notification, NotificationPreference

CATEGORY_FLAG = {
    Notification.Category.SAFETY: "safety_alerts",
    Notification.Category.BOOKING: "booking_updates",
    Notification.Category.RECOMMENDATION: "recommendations",
    Notification.Category.MARKETING: "marketing",
}
CHANNEL_FLAG = {
    Notification.Channel.IN_APP: "in_app_enabled",
    Notification.Channel.EMAIL: "email_enabled",
    Notification.Channel.SMS: "sms_enabled",
    Notification.Channel.PUSH: "push_enabled",
}


def preference_allows(user, channel, category):
    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    channel_enabled = getattr(preference, CHANNEL_FLAG[channel])
    category_enabled = getattr(preference, CATEGORY_FLAG.get(category, "in_app_enabled"), True)
    # Verified critical safety notices are never treated as marketing, but users
    # still control each delivery channel and can disable safety broadcasts.
    return channel_enabled and category_enabled


def queue_notification(user, title, message, channel="in_app", category="general", batch_id=None, metadata=None, related_alert=None):
    allowed = preference_allows(user, channel, category)
    in_app = channel == Notification.Channel.IN_APP and allowed
    return Notification.objects.create(user=user, title=title[:200], message=message, channel=channel,
        category=category, batch_id=batch_id, metadata=metadata or {}, related_alert=related_alert, is_sent=in_app,
        delivery_status=Notification.DeliveryStatus.SENT if in_app else Notification.DeliveryStatus.QUEUED if allowed else Notification.DeliveryStatus.SKIPPED,
        sent_at=timezone.now() if in_app else None,
        failure_reason="" if allowed else "Disabled by user notification preferences")


def _send(notification):
    user = notification.user
    if notification.channel == Notification.Channel.EMAIL:
        if not user.email:
            raise RuntimeError("Recipient email is unavailable")
        send_mail(notification.title, notification.message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    elif notification.channel == Notification.Channel.SMS:
        if not user.phone_number:
            raise RuntimeError("Recipient phone number is unavailable")
        if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
            raise RuntimeError("SMS provider is not configured")
        from twilio.rest import Client
        Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(
            body=notification.message[:1600], from_=settings.TWILIO_FROM_NUMBER, to=str(user.phone_number))
    elif notification.channel == Notification.Channel.PUSH:
        tokens = list(DeviceToken.objects.filter(user=user).values_list("token", flat=True))
        if not tokens:
            raise RuntimeError("No push device is registered")
        if not settings.FCM_SERVER_KEY:
            raise RuntimeError("Push provider is not configured")
        response = requests.post("https://fcm.googleapis.com/fcm/send",
            json={"registration_ids": tokens, "notification": {"title": notification.title, "body": notification.message}},
            headers={"Authorization": f"key={settings.FCM_SERVER_KEY}", "Content-Type": "application/json"}, timeout=10)
        response.raise_for_status()
    else:
        return


def deliver_notification(notification_id):
    """Attempt one queued delivery. Returns the final status for this attempt."""
    with transaction.atomic():
        notification = Notification.objects.select_for_update().select_related("user").get(pk=notification_id)
        if notification.delivery_status in {Notification.DeliveryStatus.SENT, Notification.DeliveryStatus.SKIPPED}:
            return notification.delivery_status
        notification.delivery_attempts += 1
        notification.last_attempt_at = timezone.now()
        try:
            _send(notification)
        except Exception as exc:  # provider errors are stored, never presented as success
            notification.is_sent = False
            notification.delivery_status = Notification.DeliveryStatus.FAILED
            notification.failure_reason = str(exc)[:500]
            notification.next_retry_at = (timezone.now() + timedelta(minutes=5 * (2 ** (notification.delivery_attempts - 1)))) if notification.delivery_attempts < notification.max_attempts else None
        else:
            notification.is_sent = True
            notification.delivery_status = Notification.DeliveryStatus.SENT
            notification.sent_at = timezone.now()
            notification.failure_reason = ""
            notification.next_retry_at = None
        notification.save(update_fields=["delivery_attempts", "last_attempt_at", "is_sent", "delivery_status", "failure_reason", "next_retry_at", "sent_at", "updated_at"])
        return notification.delivery_status


def process_due_notifications(limit=100):
    now = timezone.now()
    ids = list(Notification.objects.filter(delivery_status__in=["queued", "failed"], delivery_attempts__lt=models.F("max_attempts"))
        .filter(models.Q(next_retry_at__isnull=True) | models.Q(next_retry_at__lte=now)).order_by("created_at").values_list("id", flat=True)[:limit])
    counts = {"processed": 0, "sent": 0, "failed": 0}
    for notification_id in ids:
        status = deliver_notification(notification_id); counts["processed"] += 1; counts[status] = counts.get(status, 0) + 1
    return counts
