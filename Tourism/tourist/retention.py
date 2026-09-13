"""Retention and anonymization operations for protected tourism records."""
import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import (DataRetentionPolicy, DeviceToken, LocationPing, Notification,
                     RecommendationEvent, SOSAlert, UserFeedback)


def get_policy():
    return DataRetentionPolicy.objects.get_or_create(name="default")[0]


def retention_inventory(policy=None):
    from audit.models import AuditLog
    policy = policy or get_policy(); now = timezone.now()
    querysets = {
        "read_notifications": Notification.objects.filter(is_read=True, created_at__lt=now-timedelta(days=policy.read_notification_days)),
        "location_pings": LocationPing.objects.filter(recorded_at__lt=now-timedelta(days=policy.location_ping_days)),
        "recommendation_events": RecommendationEvent.objects.filter(created_at__lt=now-timedelta(days=policy.recommendation_event_days)),
        "resolved_sos": SOSAlert.objects.exclude(status="active").filter(resolved_at__lt=now-timedelta(days=policy.resolved_sos_days)),
        "routine_audit_logs": AuditLog.objects.filter(timestamp__lt=now-timedelta(days=policy.audit_log_days)).exclude(category="security").exclude(severity__in=["warning", "error", "critical"]),
    }
    return policy, querysets


def apply_retention_policy(dry_run=True):
    policy, querysets = retention_inventory()
    counts = {name: queryset.count() for name, queryset in querysets.items()}
    if not dry_run:
        with transaction.atomic():
            for queryset in querysets.values(): queryset.delete()
    return {"dry_run": dry_run, "policy": policy.name, "records": counts, "total": sum(counts.values()),
            "official_risk_preserved": policy.preserve_official_risk_records}


def anonymize_user(target, actor=None):
    """Irreversibly remove direct identifiers while preserving relational records."""
    if target.is_superuser:
        raise ValueError("Super administrator accounts cannot be anonymized")
    now=timezone.now(); old_email=target.email
    with transaction.atomic():
        if target.profile_picture:
            target.profile_picture.delete(save=False)
        target.email=f"anonymized-{target.pk}-{uuid.uuid4().hex[:12]}@deleted.invalid"
        target.first_name="Deleted";target.last_name="User";target.phone_number=None;target.phone_verified=False
        target.provider_uid="";target.bio="";target.profile_picture=None;target.latitude=None;target.longitude=None
        target.city="";target.country="";target.location_source="";target.managed_district=""
        target.is_verified=False;target.is_active=False;target.is_staff=False;target.role="tourist"
        target.deactivated_at=now;target.anonymized_at=now;target.set_unusable_password();target.save()
        DeviceToken.objects.filter(user=target).delete()
        target.notifications.all().delete();target.email_tokens.all().delete();target.sms_tokens.all().delete();target.reset_tokens.all().delete()
        target.favorites.all().delete();target.history.all().delete()
        RecommendationEvent.objects.filter(user=target).update(user=None, session_key="", query="", context={})
        UserFeedback.objects.filter(user=target).update(name="", email="")
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        OutstandingToken.objects.filter(user=target).delete()
        from audit.models import AuditLog
        AuditLog.objects.create(user=actor,user_email=actor.email if actor else None,actor_role=getattr(actor,"role",None),
            category="security",severity="warning",source="backend",action="user.anonymize",
            message=f"Anonymized user record #{target.pk}",object_type="User",object_id=str(target.pk),
            extra={"irreversible":True,"previous_email_hash":__import__('hashlib').sha256(old_email.encode()).hexdigest()})
    return target
