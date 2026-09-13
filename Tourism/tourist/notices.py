"""Published visitor notices and watcher alerts for destination pages."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .models import Favorite, TravelPlanStop, VisitorNotice

User = get_user_model()


def active_notices_qs(now=None):
    now = now or timezone.now()
    return (
        VisitorNotice.objects.filter(is_published=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .select_related("destination")
        .order_by("-updated_at")
    )


def notices_for_destination(destination, now=None):
    """Place-page notices: this destination, or the same city/district. Nationwide stay on the homepage."""
    qs = active_notices_qs(now)
    match = Q(destination=destination)
    if destination.district:
        match |= Q(destination__isnull=True, district__iexact=destination.district)
    if destination.city:
        match |= Q(destination__isnull=True, city__iexact=destination.city)
    return qs.filter(match)


def serialize_notice(notice):
    destination = notice.destination
    return {
        "id": notice.id,
        "kind": notice.kind,
        "title": notice.title,
        "body": notice.body or "",
        "city": notice.city or "",
        "district": notice.district or "",
        "destination_id": notice.destination_id,
        "destination_name": destination.name if destination else "",
        "destination_slug": destination.slug if destination else "",
        "starts_at": notice.starts_at,
        "ends_at": notice.ends_at,
    }


def notify_watchers(notice):
    """Tell travellers who saved this place about a newly published desk notice."""
    if not notice.is_published or not notice.destination_id:
        return 0
    user_ids = set(Favorite.objects.filter(destination_id=notice.destination_id).values_list("user_id", flat=True))
    user_ids.update(
        TravelPlanStop.objects.filter(destination_id=notice.destination_id)
        .exclude(plan__status="archived")
        .values_list("plan__user_id", flat=True)
    )
    if not user_ids:
        return 0
    from .models import Notification
    from .notification_delivery import queue_notification

    already_ids = set()
    for row in Notification.objects.filter(user_id__in=user_ids, channel="in_app"):
        if (row.metadata or {}).get("notice_id") == notice.id:
            already_ids.add(row.user_id)
    category = "safety" if notice.kind in {"closure", "permit", "transport"} else "general"
    title = f"{notice.get_kind_display()}: {notice.title}"[:200]
    message = (notice.body or notice.title)[:800]
    count = 0
    for user in User.objects.filter(id__in=user_ids, is_active=True).exclude(id__in=already_ids):
        queue_notification(
            user, title, message, channel="in_app", category=category,
            metadata={"notice_id": notice.id, "destination_id": notice.destination_id, "kind": notice.kind},
        )
        count += 1
    return count
