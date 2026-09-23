"""notifications/services.py — LIVE notification dispatch helpers.

This module was previously a fully-commented placeholder, which made audits
read "notifications are disabled". The real, working implementations live in
``tourist/utils.py`` (email via Django's mail backend, SMS via Twilio when
configured, push via FCM when configured, and ``notify_user`` which records a
``Notification`` and honestly stores provider delivery status).

We re-export them here so the ``notifications`` app is the canonical import
point and so ``from notifications.services import notify_user`` works. No
behaviour is duplicated or changed — this is a thin, dependency-safe alias.
"""
from tourist.utils import (  # noqa: F401
    send_email_notification,
    send_sms_notification,
    send_push_notification,
    notify_user,
)

__all__ = [
    "send_email_notification",
    "send_sms_notification",
    "send_push_notification",
    "notify_user",
]
