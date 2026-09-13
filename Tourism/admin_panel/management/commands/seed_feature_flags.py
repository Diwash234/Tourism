"""Seed the default deployment feature flags (idempotent).

Existing keys are never overwritten — admins' choices survive re-runs.

Usage:
    python manage.py seed_feature_flags
"""
from django.core.management.base import BaseCommand

from admin_panel.models import FeatureFlag

DEFAULTS = [
    ("ai_itinerary", True, "AI/dataset itinerary planner (ML service + DB fallback)"),
    ("live_navigation", True, "Turn-by-turn navigation screen with mode comparison"),
    ("offline_maps", False, "Offline map tile downloads (not shipped yet)"),
    ("voice_navigation", False, "Voice-guided navigation (not shipped yet)"),
]


class Command(BaseCommand):
    help = "Create default FeatureFlag rows without touching existing ones."

    def handle(self, *args, **options):
        created = 0
        for key, enabled, description in DEFAULTS:
            _, was_created = FeatureFlag.objects.get_or_create(
                key=key, defaults={"enabled": enabled, "description": description}
            )
            created += int(was_created)
        self.stdout.write(f"Feature flags seeded: {created} created, {len(DEFAULTS) - created} already present")
