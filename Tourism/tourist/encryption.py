"""
Encryption utilities for sensitive data.
"""
import base64
import hashlib
import logging
import os
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def encrypt_value(value: str, key: Optional[str] = None) -> str:
    """
    Encrypt a value using Fernet symmetric encryption.

    Requires: pip install cryptography
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.warning("cryptography not installed, using base64 encoding")
        return base64.b64encode(value.encode()).decode()

    key = key or getattr(settings, "ENCRYPTION_KEY", "")
    if not key:
        logger.warning("No encryption key configured")
        return base64.b64encode(value.encode()).decode()

    # Ensure key is 32 bytes for Fernet
    key_bytes = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str, key: Optional[str] = None) -> str:
    """Decrypt a value encrypted with encrypt_value."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return base64.b64decode(encrypted_value.encode()).decode()

    key = key or getattr(settings, "ENCRYPTION_KEY", "")
    if not key:
        return base64.b64decode(encrypted_value.encode()).decode()

    key_bytes = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)
    return fernet.decrypt(encrypted_value.encode()).decode()


def hash_sensitive(value: str) -> str:
    """One-way hash for sensitive data that doesn't need decryption."""
    salt = getattr(settings, "SECRET_KEY", "")
    return hashlib.sha256(f"{value}{salt}".encode()).hexdigest()


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive data, showing only the last few characters."""
    if not value:
        return ""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]
