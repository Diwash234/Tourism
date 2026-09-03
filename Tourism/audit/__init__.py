"""
audit — central audit/error/health logging for the Nepal Tourism backend.

Lazy-import helpers so callers (including settings.LOGGING handlers loaded
at Django startup, before apps are ready) can safely do:

    from audit import log_action, log_error
"""

default_app_config = "audit.apps.AuditConfig"


def log_action(*args, **kwargs):
    from .logging_services import log_action as _real
    return _real(*args, **kwargs)


def log_error(*args, **kwargs):
    from .logging_services import log_error as _real
    return _real(*args, **kwargs)
