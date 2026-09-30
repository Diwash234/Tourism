"""
Django signals for automated actions on model events.
"""
import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import User, Destination, Review
from booking.models import Booking

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a user profile when a new user is created."""
    if created:
        logger.info("New user created: %s", instance.email)
        # Create user profile, settings, etc.


@receiver(post_save, sender=Destination)
def notify_new_destination(sender, instance, created, **kwargs):
    """Notify admins when a new destination is created."""
    if created:
        logger.info("New destination created: %s", instance.name)
        # Send notification to admins


@receiver(post_save, sender=Review)
def update_destination_rating(sender, instance, created, **kwargs):
    """Update destination average rating when a new review is added."""
    if created and instance.destination:
        destination = instance.destination
        reviews = Review.objects.filter(destination=destination, is_approved=True)
        avg_rating = reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0
        destination.average_rating = round(avg_rating, 2)
        destination.review_count = reviews.count()
        destination.save(update_fields=["average_rating", "review_count", "updated_at"])


@receiver(pre_delete, sender=Destination)
def log_destination_deletion(sender, instance, **kwargs):
    """Log when a destination is deleted."""
    logger.warning("Destination deleted: %s (ID: %s)", instance.name, instance.id)
