"""
Django signals for automated actions on model events.
"""
import logging

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import User, Destination, Rating, Review
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
    """Refresh the destination's cached score counters after a new review.

    Review rows are text-only (comment + moderation_status -- no numeric
    rating and no is_approved), so the 1-5 average is read from Rating and
    written onto Destination's real fields. The previous version aggregated
    `rating`/`is_approved`, which Review does not have, and saved a
    `review_count` field Destination does not have, so creating a review
    raised FieldError and the POST 500'd.
    """
    if created and instance.destination:
        destination = instance.destination
        ratings = Rating.objects.filter(destination=destination)
        avg_rating = ratings.aggregate(models.Avg("value"))["value__avg"] or 0
        destination.average_rating = round(avg_rating, 2)
        destination.ratings_count = ratings.count()
        destination.save(update_fields=["average_rating", "ratings_count", "updated_at"])


@receiver(pre_delete, sender=Destination)
def log_destination_deletion(sender, instance, **kwargs):
    """Log when a destination is deleted."""
    logger.warning("Destination deleted: %s (ID: %s)", instance.name, instance.id)
