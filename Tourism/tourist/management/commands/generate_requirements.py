"""
Management command to generate a requirements file.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a requirements file"

    def handle(self, *args, **options):
        self.stdout.write("Generating requirements file...")

        content = """# Core
Django==6.0.7
djangorestframework==3.17.1
django-cors-headers==4.9.0
django-filter==26.1
django-phonenumber-field==8.4.0

# Authentication
djangorestframework-simplejwt==5.5.1

# Database
psycopg2-binary==2.9.13
dj-database-url==3.1.2

# Caching
django-redis==5.4.0

# Storage
django-storages==1.14.4
boto3==1.35.0

# API Documentation
drf-spectacular==0.30.0

# Real-time
channels==4.3.2
daphne==4.2.3

# Background Tasks
celery==5.4.0

# Security
cryptography==49.0.0
bcrypt==5.0.0

# Utilities
python-decouple==3.8
python-dotenv==1.2.2
Pillow==12.3.0
requests==2.34.2

# Email
django-anymail==12.0

# SMS
twilio==9.10.9

# Translation
deep-translator==1.11.4

# ML
numpy==2.5.1
scikit-learn==1.9.0
pandas==3.0.3

# Production
gunicorn==26.2.0
whitenoise==6.12.0
sentry-sdk==2.19.0
"""

        with open(Path("requirements.txt"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Requirements file generated at requirements.txt"))
