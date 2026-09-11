from django.apps import AppConfig


class TouristsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tourist"
    verbose_name = "Tourism Portal"

    def ready(self):
        import os
        import sys

        import tourist.signals  # noqa: F401

        # Background scheduler for due publications (spec §8): until now
        # scheduled pages/sections only flipped when a public-config request
        # happened to arrive. This daemon checks every 60s so publication
        # never depends on traffic. Skipped for tests/one-off commands.
        if os.environ.get("RUN_MAIN") == "true" or (
            len(sys.argv) >= 2 and sys.argv[1] == "runserver"
        ):
            import threading
            import time

            def _publish_loop():
                from django.utils import timezone

                while True:
                    time.sleep(60)
                    try:
                        from .cms_publishing import publish_due_sections
                        from .models import ManagedPage

                        now = timezone.now()
                        ManagedPage.objects.filter(
                            status="scheduled", scheduled_publish_at__lte=now
                        ).update(status="published", published_at=now, scheduled_publish_at=None)
                        publish_due_sections(now)
                    except Exception:
                        pass  # never crash the server over a tick

            threading.Thread(target=_publish_loop, daemon=True, name="cms-publish-scheduler").start()
