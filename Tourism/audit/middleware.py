"""
audit/middleware.py
-------------------
Django middleware that:
  * Writes an AuditLog entry for every state-changing request (POST/PUT/PATCH/DELETE)
  * Catches unhandled exceptions and records them in ErrorEvent with full
    request metadata (method, path, user, IP, UA, body preview).
  * Adds an `X-Request-Id` header to responses so frontend errors can be
    correlated to the backend request (used by the React error logger).

Designed to be safe: it NEVER raises exceptions.
"""
from __future__ import annotations

import logging
import time
import uuid

from django.utils import timezone

from .logging_services import log_action, log_error
from .models import ActionCategory, Severity, Source

logger = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
EXCLUDED_PATHS = ("/static/", "/media/", "/favicon", "/admin/jsi18n", "/__debug__")


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip cheap/static paths entirely
        if any(request.path.startswith(p) for p in EXCLUDED_PATHS):
            return self.get_response(request)

        request.request_id = str(uuid.uuid4())[:12]
        request.start_time = time.monotonic()

        response = None
        try:
            response = self.get_response(request)
            self._record_success(request, response)
            response["X-Request-Id"] = request.request_id
            return response
        except Exception as exc:
            self._record_exception(request, exc)
            raise
        finally:
            try:
                if response is not None:
                    duration_ms = (time.monotonic() - request.start_time) * 1000
                    # Tag slow responses as warnings in the audit log
                    if duration_ms > 2000 and request.method not in SAFE_METHODS:
                        log_action(
                            request,
                            action="request.slow",
                            category=ActionCategory.SYSTEM,
                            severity=Severity.WARNING,
                            status_code=response.status_code,
                            extra={"duration_ms": round(duration_ms, 1)},
                        )
            except Exception:  # logging must never break response
                pass

    def _record_success(self, request, response):
        if request.method in SAFE_METHODS:
            return
        # Only record user-facing API endpoints (skip admin & 4xx auth noise)
        if not request.path.startswith("/api/"):
            return
        if 200 <= response.status_code < 400:
            severity = Severity.INFO
            action = self._action_from_path(request)
            log_action(
                request, action=action,
                category=self._category_from_path(request),
                severity=severity,
                source=Source.BACKEND,
                status_code=response.status_code,
            )
        elif 400 <= response.status_code < 500:
            # Client errors are warnings, not full errors (unless auth)
            sev = Severity.WARNING
            if response.status_code in (401, 403) and "/api/auth/login" in request.path:
                sev = Severity.WARNING
            log_action(
                request, action="request.client_error",
                category=ActionCategory.SECURITY if response.status_code in (401, 403) else ActionCategory.SYSTEM,
                severity=sev,
                source=Source.BACKEND,
                status_code=response.status_code,
            )

    def _record_exception(self, request, exc):
        try:
            # Build a safe, short body preview for context
            body = ""
            try:
                if request.content_type and "application/json" in request.content_type:
                    body = (request.body or b"")[:1024].decode("utf-8", "ignore")
                elif request.content_type and "multipart" not in (request.content_type or ""):
                    body = (request.body or b"")[:512].decode("utf-8", "ignore")
            except Exception:
                body = ""
            log_error(
                request,
                exc=exc,
                source=Source.BACKEND,
                severity=Severity.ERROR,
                endpoint=request.path,
                method=request.method,
                status_code=500,
                extra={"request_id": getattr(request, "request_id", None),
                       "body_preview": body},
            )
        except Exception:
            logger.exception("audit middleware failed to record exception")

    # --- helpers -----------------------------------------------------------
    def _action_from_path(self, request):
        p = request.path
        if "/login" in p: return "auth.login"
        if "/register" in p: return "auth.register"
        if "/destinations" in p and request.method == "POST": return "destination.create"
        if "/destinations" in p and request.method in ("PUT", "PATCH"): return "destination.update"
        if "/destinations" in p and request.method == "DELETE": return "destination.delete"
        if "/admin/" in p: return "admin.request"
        return f"api.{request.method.lower()}"

    def _category_from_path(self, request):
        p = request.path
        if "/auth/" in p or "/login" in p or "/register" in p:
            return ActionCategory.AUTH
        if "/admin/" in p:
            return ActionCategory.ADMIN
        if "/images/" in p or "/media/" in p:
            return ActionCategory.MEDIA
        if "/ml/" in p or "/recommend" in p:
            return ActionCategory.ML
        return ActionCategory.DATA
