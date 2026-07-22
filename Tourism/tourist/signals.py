from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Review, Alert
from .utils import notify_user


@receiver(post_save, sender=Review)
def notify_owner_of_new_review(sender, instance, created, **kwargs):
    """Notify the destination's creator in-app when a new review comes in."""
    if not created:
        return
    owner = instance.destination.created_by
    if owner and owner != instance.user:
        notify_user(
            owner,
            title="New review on your destination",
            message=f'{instance.user.full_name} reviewed "{instance.destination.name}".',
            channel="in_app",
        )


@receiver(post_save, sender=Alert)
def notify_nearby_users_of_new_alert(sender, instance, created, **kwargs):
    """
    Notify verified users located in the same city as a newly created,
    active alert. For large user bases this should be moved to an async
    task (e.g. Celery) instead of running inline.
    """
    if not created or not instance.is_active:
        return

    from .models import User

    affected_users = User.objects.filter(is_active=True, is_verified=True, city__iexact=instance.city or "")
    for user in affected_users.iterator():
        notify_user(
            user,
            title=f"{instance.get_severity_display()} {instance.get_alert_type_display()} Alert",
            message=instance.description[:250],
            channel="in_app",
            related_alert=instance,
        )
