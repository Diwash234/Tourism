"""Security utilities for the tourism platform.

Provides:
- Rate limiting helpers
- Input sanitization
- Audit logging
- Permission checks
"""
import hashlib
import hmac
import re
import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


def rate_limit(key_prefix, limit=30, period=60):
    """Decorator to rate limit a view function.

    Args:
        key_prefix: Cache key prefix (e.g., 'search', 'chatbot')
        limit: Maximum number of requests allowed
        period: Time window in seconds

    Usage:
        @rate_limit('search', limit=30, period=60)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate unique key for this client
            client_ip = get_client_ip(request)
            cache_key = f"rate_limit:{key_prefix}:{client_ip}"

            # Get current count
            current = cache.get(cache_key, 0)

            if current >= limit:
                return JsonResponse(
                    {"error": {"code": "rate_limit_exceeded", "message": "Too many requests. Please try again later."}},
                    status=429
                )

            # Increment counter
            cache.set(cache_key, current + 1, period)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def sanitize_input(value, max_length=1000):
    """Sanitize user input to prevent XSS and injection attacks.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""

    # Truncate to max length
    value = value[:max_length]

    # Remove potentially dangerous characters
    value = re.sub(r'[<>]', '', value)

    # Normalize whitespace
    value = ' '.join(value.split())

    return value


def validate_uuid(value):
    """Validate that a string is a valid UUID."""
    if not value:
        return False
    try:
        import uuid
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def generate_secure_token(length=32):
    """Generate a cryptographically secure random token."""
    import secrets
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data):
    """Hash sensitive data for logging (never log raw PII)."""
    if not data:
        return ""
    return hashlib.sha256(str(data).encode()).hexdigest()[:16]


def verify_webhook_signature(payload, signature, secret):
    """Verify a webhook signature using HMAC-SHA256."""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def audit_log(action, user=None, details=None, ip_address=None):
    """Log a security-relevant action.

    Args:
        action: Action performed (e.g., 'login', 'password_change')
        user: User who performed the action
        details: Additional details (dict)
        ip_address: Client IP address
    """
    from audit.models import AuditLog

    AuditLog.objects.create(
        action=action,
        user=user,
        details=details or {},
        ip_address=ip_address or "",
    )


def check_permission(user, module, action="view"):
    """Check if a user has permission for a module/action.

    Args:
        user: User instance
        module: Module name (e.g., 'destinations', 'images')
        action: Action name (e.g., 'view', 'change', 'delete')

    Returns:
        True if permitted, False otherwise
    """
    if not user or not user.is_authenticated:
        return False

    # Super admins have all permissions
    if user.is_superuser:
        return True

    # Check staff capability profile
    profile = getattr(user, 'capability_profile', None)
    if profile and profile.is_active:
        return profile.allows(module, action)

    return False


def require_permission(module, action="view"):
    """Decorator to require a specific permission."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not check_permission(request.user, module, action):
                return JsonResponse(
                    {"error": {"code": "permission_denied", "message": "You do not have permission to perform this action."}},
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
