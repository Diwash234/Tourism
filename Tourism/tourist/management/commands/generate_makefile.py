"""
Management command to generate a Makefile.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Makefile"

    def handle(self, *args, **options):
        self.stdout.write("Generating Makefile...")

        content = """.PHONY: install test run migrate seed backup restore clean

install:
\tpip install -r Tourism/requirements.txt
\tcd frontend/Tourism && npm install

test:
\tcd Tourism && python manage.py test --noinput

run:
\tcd Tourism && python manage.py runserver

migrate:
\tcd Tourism && python manage.py migrate

seed:
\tcd Tourism && python manage.py seed_data

backup:
\tcd Tourism && python manage.py backup_db

restore:
\tcd Tourism && python manage.py restore_db --file=backup.json

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {} +
\tfind . -type f -name "*.pyc" -delete

docker-build:
\tdocker build -t tourism-platform .

docker-run:
\tdocker-compose up

docker-stop:
\tdocker-compose down

lint:
\tcd Tourism && python -m flake8 .
\tcd frontend/Tourism && npm run lint

format:
\tcd Tourism && python -m black .
\tcd frontend/Tourism && npm run format
"""

        with open(Path("Makefile"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Makefile generated"))
