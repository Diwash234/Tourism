"""
Django signals for automated actions on model events.
"""
import logging

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import User, Destination, Rating, Review, Alert, FamilyLink
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


@receiver(post_save, sender=Alert)
def notify_geofenced_alert(sender, instance, created, **kwargs):
    """Push a new verified alert to everyone inside its geofence.

    Users with a recorded position within ``radius_km`` of the alert get a
    "Nearby alert" notification; contacts linked through an accepted
    FamilyLink get the same notice with ``related_alert`` set so the safety
    feed can attribute it (test_geofenced_alert_notifies_nearby_user_and_family).
    Unverified/inactive alerts and alerts without coordinates are skipped,
    and fixture loads (loaddata) never fire this - they save raw.
    """
    if not created or not instance.is_active or not instance.is_verified:
        return
    if instance.latitude is None or instance.longitude is None:
        return

    from .notification_delivery import queue_notification
    from .utils import haversine_distance

    lat, lon = float(instance.latitude), float(instance.longitude)
    radius_km = float(instance.radius_km or 0)
    nearby = []
    for user in User.objects.filter(
        is_active=True, latitude__isnull=False, longitude__isnull=False
    ).exclude(latitude=0, longitude=0):
        distance = haversine_distance(lat, lon, float(user.latitude), float(user.longitude))
        if distance is not None and distance <= radius_km:
            nearby.append(user)
    if not nearby:
        return

    title = f"Nearby alert: {instance.title}"
    message = (instance.description or "").strip() or instance.title
    notified = set()
    for user in nearby:
        queue_notification(user, title, message, category="safety", related_alert=instance)
        notified.add(user.id)

    nearby_ids = {user.id for user in nearby}
    links = FamilyLink.objects.filter(status=FamilyLink.Status.ACCEPTED).filter(
        models.Q(requester_id__in=nearby_ids) | models.Q(member_id__in=nearby_ids)
    ).select_related("requester", "member")
    for link in links:
        other = link.member if link.requester_id in nearby_ids else link.requester
        if other.id in notified:
            continue
        queue_notification(
            other,
            f"Safety alert near your contact: {instance.title}",
            message,
            category="safety",
            related_alert=instance,
        )
        notified.add(other.id)
    logger.info("Alert %s geofence notified %d user(s)", instance.pk, len(notified))


@receiver(pre_delete, sender=Destination)
def log_destination_deletion(sender, instance, **kwargs):
    """Log when a destination is deleted."""
    logger.warning("Destination deleted: %s (ID: %s)", instance.name, instance.id)
