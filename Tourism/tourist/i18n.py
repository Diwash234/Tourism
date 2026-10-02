"""
Internationalization utilities.
"""
import logging
from functools import wraps
from typing import Optional

from django.utils import translation
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def get_current_language() -> str:
    """Get the current active language."""
    return translation.get_language()


def set_language(lang: str):
    """Set the active language."""
    translation.activate(lang)


def translate_text(text: str, target_lang: str, source_lang: str = "en") -> str:
    """Translate text using the configured translation service."""
    try:
        from .utils import translate_text as _translate
        return _translate(text, target_lang, source_lang)
    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        return text


def localized_response(data: dict, lang: Optional[str] = None) -> dict:
    """Return a localized response."""
    if lang:
        set_language(lang)
    return {
        "data": data,
        "language": get_current_language(),
    }


def with_language(lang: str):
    """Decorator to set language for a view."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            old_lang = get_current_language()
            set_language(lang)
            try:
                return func(*args, **kwargs)
            finally:
                set_language(old_lang)
        return wrapper
    return decorator
