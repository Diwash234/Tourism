"""
Management command to generate OpenAPI specification.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate OpenAPI specification"

    def handle(self, *args, **options):
        self.stdout.write("Generating OpenAPI specification...")

        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """openapi: 3.0.0
info:
  title: Nepal Tourism Platform API
  description: REST API for the Nepal Tourism Platform
  version: 1.0.0
servers:
  - url: https://your-domain.com/api/v1
paths:
  /auth/register/:
    post:
      summary: Register a new user
      responses:
        '201':
          description: User created
  /auth/login/:
    post:
      summary: Login
      responses:
        '200':
          description: Login successful
  /destinations/:
    get:
      summary: List all destinations
      responses:
        '200':
          description: List of destinations
  /destinations/{slug}/:
    get:
      summary: Get destination details
      parameters:
        - name: slug
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Destination details
  /health/:
    get:
      summary: Health check
      responses:
        '200':
          description: System is healthy
"""

        with open(docs_dir / "openapi.yaml", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"OpenAPI spec generated at {docs_dir / 'openapi.yaml'}"))
