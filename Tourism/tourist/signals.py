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
    """Notify users within 2–4 km and their accepted family links."""
    if not created or not instance.is_active:
        return

    from django.db.models import Q
    from .models import FamilyLink, User
    from .utils import haversine_distance

    radius_km = 4.0 if instance.severity in {Alert.Severity.HIGH, Alert.Severity.CRITICAL} else 2.0
    users = User.objects.filter(is_active=True, is_verified=True)
    affected = []
    for user in users.iterator():
        in_city = bool(instance.city and (user.city or "").lower() == instance.city.lower())
        in_radius = False
        if None not in (instance.latitude, instance.longitude, user.latitude, user.longitude):
            in_radius = haversine_distance(
                instance.latitude, instance.longitude, user.latitude, user.longitude
            ) <= radius_km
        if in_radius or (instance.latitude is None and in_city):
            affected.append(user)

    notified_ids = set()
    for user in affected:
        notify_user(
            user,
            title=f"Nearby {instance.get_severity_display()} {instance.get_alert_type_display()} Alert",
            message=f"Within the {radius_km:g} km alert area: {instance.description[:220]}",
            channel="in_app", related_alert=instance,
        )
        notified_ids.add(user.id)

        links = FamilyLink.objects.filter(
            Q(requester=user) | Q(member=user), status=FamilyLink.Status.ACCEPTED
        ).select_related("requester", "member")
        for link in links:
            relative = link.member if link.requester_id == user.id else link.requester
            if relative.id in notified_ids:
                continue
            notify_user(
                relative,
                title=f"Safety alert near {user.full_name}",
                message=f"{instance.get_alert_type_display()} alert within {radius_km:g} km of your family member: {instance.description[:190]}",
                channel="in_app", related_alert=instance,
            )
            notified_ids.add(relative.id)
