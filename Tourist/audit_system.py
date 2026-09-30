"""Audit system for tracking data changes.

Provides:
- Log all data changes (create, update, delete)
- Track who made changes and when
- Support rollback of changes
- Audit trail queries
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Destination, DestinationAuditLog

logger = logging.getLogger(__name__)


def log_change(model, instance, action, user=None, field_changes=None, reason=None):
    """Log a data change.

    Args:
        model: Model class
        instance: Model instance
        action: Action type ('create', 'update', 'delete')
        user: User who made the change
        field_changes: List of field changes [{'field': 'name', 'old': '...', 'new': '...'}]
        reason: Reason for the change

    Returns:
        DestinationAuditLog instance
    """
    try:
        # Get current and previous status
        previous_status = getattr(instance, 'status', '')
        new_status = getattr(instance, 'status', '')

        # Create audit log
        audit = DestinationAuditLog.objects.create(
            destination=instance if isinstance(instance, Destination) else None,
            action=action,
            actor=user,
            field_changes=field_changes or [],
            previous_status=previous_status,
            new_status=new_status,
            reason=reason or '',
        )

        logger.info(f"Audit log created: {audit}")
        return audit

    except Exception as exc:
        logger.error(f"Error logging change: {exc}")
        return None


def get_audit_trail(model, instance_id, limit=50):
    """Get audit trail for a specific instance.

    Args:
        model: Model class
        instance_id: Instance ID
        limit: Maximum number of entries

    Returns:
        QuerySet of audit logs
    """
    try:
        if isinstance(model, Destination):
            return DestinationAuditLog.objects.filter(
                destination_id=instance_id
            ).order_by('-created_at')[:limit]
        return []
    except Exception as exc:
        logger.error(f"Error getting audit trail: {exc}")
        return []


def rollback_change(audit_id):
    """Rollback a change.

    Args:
        audit_id: Audit log ID

    Returns:
        True if rollback successful
    """
    try:
        audit = DestinationAuditLog.objects.get(id=audit_id)

        if not audit.destination:
            raise ValueError("Cannot rollback: no destination associated")

        # Restore previous values
        if audit.field_changes:
            for change in audit.field_changes:
                field = change['field']
                old_value = change['old']
                setattr(audit.destination, field, old_value)

            audit.destination.save()

        # Log the rollback
        DestinationAuditLog.objects.create(
            destination=audit.destination,
            action='rollback',
            actor=audit.actor,
            note=f"Rolled back change from {audit.created_at}",
        )

        logger.info(f"Rollback successful for audit {audit_id}")
        return True

    except Exception as exc:
        logger.error(f"Error rolling back change: {exc}")
        return False


def get_recent_changes(hours=24, user=None):
    """Get recent changes.

    Args:
        hours: Number of hours to look back
        user: Filter by user

    Returns:
        QuerySet of audit logs
    """
    try:
        since = timezone.now() - timedelta(hours=hours)
        queryset = DestinationAuditLog.objects.filter(created_at__gte=since)

        if user:
            queryset = queryset.filter(actor=user)

        return queryset.order_by('-created_at')

    except Exception as exc:
        logger.error(f"Error getting recent changes: {exc}")
        return []


def get_change_stats(days=7):
    """Get change statistics.

    Args:
        days: Number of days to analyze

    Returns:
        Dict with statistics
    """
    try:
        since = timezone.now() - timedelta(days=days)

        total = DestinationAuditLog.objects.filter(created_at__gte=since).count()
        by_action = {}
        by_user = {}

        for log in DestinationAuditLog.objects.filter(created_at__gte=since):
            # Count by action
            action = log.action
            by_action[action] = by_action.get(action, 0) + 1

            # Count by user
            user = log.actor.email if log.actor else 'system'
            by_user[user] = by_user.get(user, 0) + 1

        return {
            'total_changes': total,
            'by_action': by_action,
            'by_user': by_user,
            'period_days': days,
        }

    except Exception as exc:
        logger.error(f"Error getting change stats: {exc}")
        return {}


def cleanup_old_logs(days=365):
    """Clean up old audit logs.

    Args:
        days: Number of days to keep

    Returns:
        Number of logs deleted
    """
    try:
        cutoff = timezone.now() - timedelta(days=days)
        old_logs = DestinationAuditLog.objects.filter(created_at__lt=cutoff)
        count = old_logs.count()
        old_logs.delete()

        logger.info(f"Cleaned up {count} old audit logs")
        return count

    except Exception as exc:
        logger.error(f"Error cleaning up old logs: {exc}")
        return 0
