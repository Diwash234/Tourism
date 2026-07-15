from django.apps import AppConfig


class TouristConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tourist"
    verbose_name = "Tourism Portal"

    def ready(self):
        from . import signals
