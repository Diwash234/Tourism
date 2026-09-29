"""
Custom exception handler for the Tourism API.

Provides a consistent error response format across all API endpoints:
    {"error": {"code": str, "message": str, "details": dict}}

Handles ValidationError, PermissionDenied, NotFound, and generic Exception.
Logs all errors with request context for debugging.
"""
import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom DRF exception handler.

    Returns a consistent error format for all exceptions:
        {"error": {"code": str, "message": str, "details": dict}}

    Logs all errors with request context (path, method, user) for debugging.
    """
    request = context.get("request") if context else None

    # Log the error with request context
    _log_error(exc, request)

    # Map exception types to consistent error responses
    if isinstance(exc, ValidationError):
        return _handle_validation_error(exc)
    if isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
        return _handle_permission_denied(exc)
    if isinstance(exc, (NotFound, Http404)):
        return _handle_not_found(exc)
    if isinstance(exc, APIException):
        return _handle_api_exception(exc)

    # Fall back to DRF's default handler first
    response = exception_handler(exc, context)
    if response is not None:
        return _format_response(response, exc)

    # Generic unhandled exception
    return _handle_generic_exception(exc)


def _log_error(exc, request):
    """Log error with request context."""
    user = getattr(request, "user", None)
    user_info = f"user={user.email}" if user and user.is_authenticated else "anonymous"
    path = getattr(request, "path", "unknown") if request else "unknown"
    method = getattr(request, "method", "unknown") if request else "unknown"

    logger.error(
        "API error at %s %s [%s]: %s: %s",
        method,
        path,
        user_info,
        exc.__class__.__name__,
        str(exc),
        exc_info=True,
    )


def _handle_validation_error(exc):
    """Handle DRF ValidationError."""
    if isinstance(exc.detail, dict):
        details = exc.detail
        message = "Validation failed. Check 'details' for field-specific errors."
    elif isinstance(exc.detail, list):
        details = {"errors": exc.detail}
        message = str(exc.detail[0]) if exc.detail else "Validation failed."
    else:
        details = {"error": str(exc.detail)}
        message = str(exc.detail)

    return Response(
        {"error": {"code": "validation_error", "message": message, "details": details}},
        status=status.HTTP_400_BAD_REQUEST,
    )


def _handle_permission_denied(exc):
    """Handle permission denied errors."""
    message = str(exc.detail) if hasattr(exc, "detail") else str(exc)
    if not message or message == "Forbidden":
        message = "You do not have permission to perform this action."
    return Response(
        {"error": {"code": "permission_denied", "message": message, "details": {}}},
        status=status.HTTP_403_FORBIDDEN,
    )


def _handle_not_found(exc):
    """Handle not found errors."""
    message = str(exc.detail) if hasattr(exc, "detail") else str(exc)
    if not message or message == "Not found.":
        message = "The requested resource was not found."
    return Response(
        {"error": {"code": "not_found", "message": message, "details": {}}},
        status=status.HTTP_404_NOT_FOUND,
    )


def _handle_api_exception(exc):
    """Handle other DRF API exceptions."""
    message = str(exc.detail) if hasattr(exc, "detail") else str(exc)
    code = exc.__class__.__name__.lower().replace("exception", "")
    return Response(
        {"error": {"code": code, "message": message, "details": {}}},
        status=exc.status_code,
    )


def _handle_generic_exception(exc):
    """Handle unhandled/generic exceptions."""
    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _format_response(response, exc):
    """Format a DRF response into the consistent error format."""
    if isinstance(response.data, dict) and "detail" in response.data:
        message = response.data["detail"]
    elif isinstance(response.data, dict):
        message = "Request failed."
    else:
        message = str(response.data)

    code = exc.__class__.__name__.lower().replace("exception", "")
    return Response(
        {"error": {"code": code, "message": message, "details": response.data if isinstance(response.data, dict) else {}}},
        status=response.status_code,
    )
