"""
Application configuration and feature flags.
"""
from django.conf import settings


class FeatureFlags:
    """
    Feature flags for enabling/disabling features.

    Usage:
        if FeatureFlags.is_enabled("advanced_search"):
            # do advanced search
    """

    DEFAULTS = {
        "advanced_search": True,
        "real_time_notifications": False,
        "recommendations": True,
        "reviews": True,
        "favorites": True,
        "travel_plans": True,
        "booking": True,
        "chatbot": True,
        "weather": True,
        "maps": True,
        "analytics": True,
        "export": True,
        "bulk_operations": True,
        "webhooks": False,
        "maintenance_mode": False,
    }

    @classmethod
    def is_enabled(cls, feature: str) -> bool:
        """Check if a feature is enabled."""
        return getattr(settings, "FEATURE_FLAGS", {}).get(
            feature, cls.DEFAULTS.get(feature, False)
        )

    @classmethod
    def enable(cls, feature: str):
        """Enable a feature."""
        if not hasattr(settings, "FEATURE_FLAGS"):
            settings.FEATURE_FLAGS = {}
        settings.FEATURE_FLAGS[feature] = True

    @classmethod
    def disable(cls, feature: str):
        """Disable a feature."""
        if not hasattr(settings, "FEATURE_FLAGS"):
            settings.FEATURE_FLAGS = {}
        settings.FEATURE_FLAGS[feature] = False

    @classmethod
    def get_all(cls) -> dict:
        """Get all feature flags."""
        flags = cls.DEFAULTS.copy()
        flags.update(getattr(settings, "FEATURE_FLAGS", {}))
        return flags
