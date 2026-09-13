"""
audit/logging_services.py
-------------------------
Python helpers used throughout the codebase to write audit events and
record errors without coupling every view to the ORM directly.

All Django model imports are LOCAL so that this module can be imported
during settings.LOGGING configuration (before apps are ready) without
raising ``AppRegistryNotReady``.

Usage:
    from audit.logging_services import log_action, log_error
    log_action(request, "destination.create", category="data", ...)
    log_error(request, exc, endpoint=request.path)
"""
from __future__ import annotations

import hashlib
import logging
import traceback
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

# Lazy reference so we don't touch the ORM at import time
ErrorEvent = None
AuditLog = None
ActionCategory = None
Severity = None
Source = None

logger = logging.getLogger(__name__)


def _models():
    """Import audit.models on demand."""
    global ErrorEvent, AuditLog, ActionCategory, Severity, Source
    if ErrorEvent is None:
        from .models import (  # noqa: WPS433 (intentional lazy import)
            ActionCategory as AC, AuditLog as AL, ErrorEvent as EE,
            Severity as S, Source as SRC,
        )
        ErrorEvent, AuditLog, ActionCategory, Severity, Source = EE, AL, AC, S, SRC
    return ErrorEvent, AuditLog, ActionCategory, Severity, Source


# ---------------------------------------------------------------------------
# Audit actions
# ---------------------------------------------------------------------------
def _client_ip(request) -> str | None:
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(
    request=None,
    action: str = "",
    *,
    category: str = "other",
    severity: str = "info",
    source: str = "backend",
    message: str = "",
    obj=None,
    object_type: str | None = None,
    object_id: Any = None,
    status_code: int | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    extra: dict | None = None,
    user=None,
) -> AuditLog:
    """Persist a structured audit entry. Safe to call anywhere."""
    _E, _A, AC, SEV, SRC = _models()
    g = globals()
    g["ActionCategory"], g["Severity"], g["Source"] = AC, SEV, SRC
    category = category if category != "other" else AC.OTHER
    severity = severity if severity != "info" else SEV.INFO
    source = source if source != "backend" else SRC.BACKEND
    user = user or getattr(request, "user", None) if request else None
    if user and not getattr(user, "is_authenticated", False):
        user = None

    if obj is not None:
        object_type = object_type or obj.__class__.__name__
        object_id = object_id or getattr(obj, "pk", None)

    entry = AuditLog(
        user=user,
        user_email=getattr(user, "email", None),
        ip_address=_client_ip(request),
        actor_role=getattr(user, "role", None) if user else None,
        category=category,
        severity=severity,
        source=source,
        action=action,
        message=message,
        object_type=object_type or "",
        object_id=str(object_id) if object_id is not None else None,
        endpoint=endpoint or (getattr(request, "path", None) if request else None),
        method=method or (getattr(request, "method", None) if request else None),
        status_code=status_code,
        extra=extra or {},
    )
    try:
        entry.save()
    except Exception:  # never break the request because of logging
        logger.exception("audit.log_action failed")
    return entry


# ---------------------------------------------------------------------------
# Error recording
# ---------------------------------------------------------------------------
def _fingerprint(source, error_type, endpoint, message):
    raw = f"{source}|{error_type}|{endpoint or ''}|{(message or '')[:80]}"
    return hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:40]


def log_error(
    request=None,
    exc: BaseException | None = None,
    *,
    source: str = "backend",
    severity: str = "error",
    error_type: str | None = None,
    error_message: str | None = None,
    traceback_text: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    status_code: int | None = None,
    component: str | None = None,
    user=None,
    extra: dict | None = None,
    user_agent: str | None = None,
    referer: str | None = None,
    merge_window_seconds: int = 300,
) -> ErrorEvent:
    """Record an error, merging duplicates within `merge_window_seconds`."""
    from django.db import IntegrityError, OperationalError
    _E, _A, AC, SEV, SRC = _models()
    g = globals()
    g["ErrorEvent"], g["AuditLog"], g["ActionCategory"], g["Severity"], g["Source"] = _E, _A, AC, SEV, SRC
    severity = severity if severity != "error" else SEV.ERROR
    source = source if source != "backend" else SRC.BACKEND
    user = user or getattr(request, "user", None) if request else None
    if user and not getattr(user, "is_authenticated", False):
        user = None

    if exc is not None:
        error_type = error_type or exc.__class__.__name__
        error_message = error_message or str(exc)
        if traceback_text is None:
            traceback_text = "".join(traceback.format_exception(
                type(exc), exc, exc.__traceback__
            ))
    error_type = error_type or "UnknownError"
    error_message = error_message or ""

    endpoint = endpoint or (getattr(request, "path", None) if request else None)
    method = method or (getattr(request, "method", None) if request else None)
    if request is not None:
        user_agent = user_agent or request.META.get("HTTP_USER_AGENT", "")
        referer = referer or request.META.get("HTTP_REFERER", "")

    fp = _fingerprint(source, error_type, endpoint, error_message)

    # Attempt to dedupe within the time window
    cutoff = timezone.now() - timezone.timedelta(seconds=merge_window_seconds)
    try:
        existing = ErrorEvent.objects.filter(
            fingerprint=fp, resolved=False, last_seen__gte=cutoff,
        ).first()
        if existing:
            existing.occurrences += 1
            existing.last_seen = timezone.now()
            if error_message and not existing.error_message:
                existing.error_message = error_message
            if traceback_text and not existing.traceback:
                existing.traceback = traceback_text
            existing.save(update_fields=[
                "occurrences", "last_seen", "error_message", "traceback",
            ])
            return existing

        ev = ErrorEvent(
            source=source,
            severity=severity,
            error_type=error_type,
            error_message=error_message[:4000],
            traceback=traceback_text or "",
            fingerprint=fp,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            user=user,
            user_email=getattr(user, "email", None),
            ip_address=_client_ip(request),
            user_agent=user_agent or "",
            referer=referer,
            component=component,
            extra=extra or {},
        )
        ev.save()
        return ev
    except (IntegrityError, OperationalError):
        # Database may not be ready during migrations/tests - just log to stderr
        logger.exception("audit.log_error failed to save")
        return ErrorEvent(
            error_type=error_type, error_message=error_message, source=source,
        )


# ---------------------------------------------------------------------------
# Logging handler that routes logging.error/exception calls into ErrorEvent
# ---------------------------------------------------------------------------
class AuditDBHandler(logging.Handler):
    """File-safe handler: it imports the ORM lazily so that Django's logging
    configuration (which runs before apps are loaded) does not fail."""

    def emit(self, record: logging.LogRecord):
        if record.levelno < logging.WARNING:
            return
        try:
            _E, _A, AC, SEV, SRC = _models()
            globals()["ErrorEvent"] = _E
            # Resolve models lazily; if apps aren't ready yet (startup) just skip
            import django
            from django.apps import apps
            if not apps.ready or not django.db.connection.introspection:
                return
            err = record.exc_info[1] if record.exc_info else None
            log_error(
                exc=err,
                source=SRC.BACKEND,
                severity=(SEV.CRITICAL if record.levelno >= logging.CRITICAL
                          else SEV.ERROR if record.levelno >= logging.ERROR
                          else SEV.WARNING),
                error_type=record.name,
                error_message=self.format(record)[:4000],
                endpoint=getattr(record, "endpoint", None),
                component=record.module,
                traceback_text=self.format(record) if record.exc_info else "",
                merge_window_seconds=600,
            )
        except Exception:
            pass  # never raise from a logging handler
