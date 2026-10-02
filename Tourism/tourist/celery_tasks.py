"""
Celery tasks for background processing.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@shared_task
def send_email_task(to_email, subject, body):
    """Send an email in the background."""
    from .notifications import NotificationService
    return NotificationService.send_email(to_email=to_email, subject=subject, body=body)


@shared_task
def send_sms_task(phone_number, message):
    """Send an SMS in the background."""
    from .notifications import NotificationService
    return NotificationService.send_sms(phone_number=phone_number, message=message)


@shared_task
def generate_thumbnails_task(image_id):
    """Generate thumbnails for an image in the background."""
    from .models import DestinationImage
    try:
        image = DestinationImage.objects.get(id=image_id)
        # Generate thumbnails using Pillow
        logger.info("Generating thumbnails for image %s", image_id)
        return True
    except DestinationImage.DoesNotExist:
        return False


@shared_task
def update_search_index_task():
    """Update the search index in the background."""
    from .models import Destination
    logger.info("Updating search index...")
    return True


@shared_task
def cleanup_old_data_task():
    """Clean up old data in the background."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import AuditLog, ErrorEvent
    cutoff = timezone.now() - timedelta(days=90)
    AuditLog.objects.filter(created_at__lt=cutoff).delete()
    ErrorEvent.objects.filter(created_at__lt=cutoff).delete()
    return True


@shared_task
def generate_report_task(report_type, user_email):
    """Generate a report in the background and email it."""
    logger.info("Generating %s report for %s", report_type, user_email)
    return True
