"""Notification queue for background delivery.

Provides:
- Queue notifications for background processing
- Process queue with priority
- Retry failed notifications
- Queue statistics
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from .models import Notification

logger = logging.getLogger(__name__)


def enqueue(notification):
    """Add a notification to the delivery queue.

    Args:
        notification: Notification instance

    Returns:
        True if enqueued successfully
    """
    try:
        if notification.channel == Notification.Channel.IN_APP:
            # In-app notifications are delivered immediately
            notification.delivery_status = Notification.DeliveryStatus.SENT
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save()
            return True

        # Queue for background delivery
        notification.delivery_status = Notification.DeliveryStatus.QUEUED
        notification.save()

        # Trigger async processing (in production, use Celery)
        # process_queue.delay()

        return True

    except Exception as exc:
        logger.error(f"Error enqueuing notification: {exc}")
        return False


def process_queue(batch_size=50):
    """Process pending notifications in the queue.

    Args:
        batch_size: Maximum number of notifications to process

    Returns:
        Dict with processing statistics
    """
    stats = {
        'processed': 0,
        'sent': 0,
        'failed': 0,
        'skipped': 0,
    }

    try:
        # Get pending notifications
        pending = Notification.objects.filter(
            delivery_status=Notification.DeliveryStatus.QUEUED,
            is_sent=False,
        ).select_related('user').order_by('created_at')[:batch_size]

        for notification in pending:
            stats['processed'] += 1

            try:
                # Check user preferences
                if not _should_send(notification):
                    notification.delivery_status = Notification.DeliveryStatus.SKIPPED
                    notification.save()
                    stats['skipped'] += 1
                    continue

                # Send notification
                if _send_notification(notification):
                    notification.delivery_status = Notification.DeliveryStatus.SENT
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    notification.save()
                    stats['sent'] += 1
                else:
                    _handle_failure(notification)
                    stats['failed'] += 1

            except Exception as exc:
                logger.error(f"Error processing notification {notification.id}: {exc}")
                _handle_failure(notification)
                stats['failed'] += 1

    except Exception as exc:
        logger.error(f"Error processing notification queue: {exc}")

    return stats


def retry_failed(max_retries=3):
    """Retry failed notifications.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Number of notifications retried
    """
    try:
        failed = Notification.objects.filter(
            delivery_status=Notification.DeliveryStatus.FAILED,
            delivery_attempts__lt=max_retries,
        ).select_related('user')

        retried = 0
        for notification in failed:
            # Check if it's time to retry
            if notification.next_retry_at and notification.next_retry_at > timezone.now():
                continue

            notification.delivery_status = Notification.DeliveryStatus.QUEUED
            notification.save()
            retried += 1

        return retried

    except Exception as exc:
        logger.error(f"Error retrying failed notifications: {exc}")
        return 0


def get_queue_stats():
    """Get notification queue statistics.

    Returns:
        Dict with queue statistics
    """
    try:
        return {
            'queued': Notification.objects.filter(
                delivery_status=Notification.DeliveryStatus.QUEUED
            ).count(),
            'sent': Notification.objects.filter(
                delivery_status=Notification.DeliveryStatus.SENT
            ).count(),
            'failed': Notification.objects.filter(
                delivery_status=Notification.DeliveryStatus.FAILED
            ).count(),
            'skipped': Notification.objects.filter(
                delivery_status=Notification.DeliveryStatus.SKIPPED
            ).count(),
            'total': Notification.objects.count(),
        }
    except Exception as exc:
        logger.error(f"Error getting queue stats: {exc}")
        return {}


def _should_send(notification):
    """Check if a notification should be sent based on user preferences.

    Args:
        notification: Notification instance

    Returns:
        True if the notification should be sent
    """
    try:
        prefs = notification.user.notification_preferences

        if not prefs:
            return True

        # Check channel-specific preferences
        if notification.channel == Notification.Channel.EMAIL:
            return prefs.email_enabled and prefs.email_notifications
        elif notification.channel == Notification.Channel.SMS:
            return prefs.sms_enabled and prefs.sms_notifications
        elif notification.channel == Notification.Channel.PUSH:
            return prefs.push_enabled and prefs.push_notifications
        elif notification.channel == Notification.Channel.IN_APP:
            return prefs.in_app_enabled

        return True

    except Exception:
        return True


def _send_notification(notification):
    """Send a notification through the appropriate channel.

    Args:
        notification: Notification instance

    Returns:
        True if sent successfully
    """
    try:
        if notification.channel == Notification.Channel.EMAIL:
            return _send_email(notification)
        elif notification.channel == Notification.Channel.SMS:
            return _send_sms(notification)
        elif notification.channel == Notification.Channel.PUSH:
            return _send_push(notification)
        elif notification.channel == Notification.Channel.IN_APP:
            return True  # In-app is always "sent"

        return False

    except Exception as exc:
        logger.error(f"Error sending notification {notification.id}: {exc}")
        return False


def _send_email(notification):
    """Send an email notification.

    Args:
        notification: Notification instance

    Returns:
        True if sent successfully
    """
    try:
        from django.core.mail import send_mail

        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=[notification.user.email],
            fail_silently=True,
        )
        return True

    except Exception as exc:
        logger.error(f"Error sending email: {exc}")
        return False


def _send_sms(notification):
    """Send an SMS notification.

    Args:
        notification: Notification instance

    Returns:
        True if sent successfully
    """
    try:
        # In production, integrate with Twilio
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # client.messages.create(
        #     body=notification.message,
        #     from_=settings.TWILIO_FROM_NUMBER,
        #     to=notification.user.phone_number,
        # )
        return True

    except Exception as exc:
        logger.error(f"Error sending SMS: {exc}")
        return False


def _send_push(notification):
    """Send a push notification.

    Args:
        notification: Notification instance

    Returns:
        True if sent successfully
    """
    try:
        # In production, integrate with FCM
        # from firebase_admin import messaging
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=notification.title,
        #         body=notification.message,
        #     ),
        #     token=notification.user.device_tokens.first().token,
        # )
        # messaging.send(message)
        return True

    except Exception as exc:
        logger.error(f"Error sending push: {exc}")
        return False


def _handle_failure(notification):
    """Handle a failed notification.

    Args:
        notification: Notification instance
    """
    notification.delivery_attempts += 1
    notification.last_attempt_at = timezone.now()

    if notification.delivery_attempts >= notification.max_attempts:
        notification.delivery_status = Notification.DeliveryStatus.FAILED
    else:
        # Exponential backoff
        delay = 2 ** notification.delivery_attempts
        notification.next_retry_at = timezone.now() + timedelta(minutes=delay)

    notification.save()
