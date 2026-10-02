"""
Management command to generate a Celery configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Celery configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Celery configuration...")

        content = """# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ACCEPT_CONTENT=['json']
CELERY_TASK_SERIALIZER='json'
CELERY_RESULT_SERIALIZER='json'
CELERY_TIMEZONE='UTC'
CELERY_ENABLE_UTC=True

# Task routes
CELERY_TASK_ROUTES = {
    'tourist.celery_tasks.send_email_task': {'queue': 'email'},
    'tourist.celery_tasks.send_sms_task': {'queue': 'sms'},
    'tourist.celery_tasks.generate_thumbnails_task': {'queue': 'images'},
}

# Beat schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-data': {
        'task': 'tourist.celery_tasks.cleanup_old_data_task',
        'schedule': 86400.0,  # Daily
    },
    'update-search-index': {
        'task': 'tourist.celery_tasks.update_search_index_task',
        'schedule': 3600.0,  # Hourly
    },
}
"""

        with open(Path("celeryconfig.py"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Celery configuration generated at celeryconfig.py"))
