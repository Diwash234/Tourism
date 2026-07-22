"""
Pulls the list of locally-supported languages from the ML service's
/languages endpoint (backed by model/translation_engine.py::supported_languages())
and upserts them into Django's Language table, so the frontend's language
picker (GET /api/v1/languages/) automatically reflects whatever your
dataset actually covers.

Usage:
    python manage.py sync_languages
"""
from django.core.management.base import BaseCommand

from tourist.models import Language
from tourist.utils import get_ml_supported_languages


class Command(BaseCommand):
    help = "Syncs Language rows from the ML service's local-language dataset."

    def handle(self, *args, **options):
        languages = get_ml_supported_languages()
        if not languages:
            self.stdout.write(self.style.WARNING(
                "No languages returned — is the ML service running (ML_SERVICE_URL in .env)?"
            ))
            return

        created, updated = 0, 0
        for lang in languages:
            obj, was_created = Language.objects.update_or_create(
                code=lang["code"], defaults={"name": lang["name"], "is_active": True}
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(f"Synced languages: {created} created, {updated} updated."))
