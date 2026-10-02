"""
Management command to generate a Docker Compose file.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Docker Compose file"

    def handle(self, *args, **options):
        self.stdout.write("Generating Docker Compose file...")

        content = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://postgres:postgres@db:5432/tourism
      - SECRET_KEY=change-me-in-production
    depends_on:
      - db
      - redis

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=tourism
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  ml-service:
    build: ./ml_service
    ports:
      - "8001:8001"
    environment:
      - ML_SERVICE_PORT=8001

volumes:
  postgres_data:
"""

        with open(Path("docker-compose.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Docker Compose file generated at docker-compose.yml"))
