from django.apps import AppConfig


class TouristsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tourist"
    verbose_name = "Tourism Portal"

    def ready(self):
        import tourist.signals  # noqa: F401
