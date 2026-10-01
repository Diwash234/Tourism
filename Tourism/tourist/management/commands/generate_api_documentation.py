"""
Management command to generate API documentation.
"""
from pathlib import Path

from django.core.management.base import BaseCommand
from django.urls import get_resolver


class Command(BaseCommand):
    help = "Generate API documentation"

    def handle(self, *args, **options):
        self.stdout.write("Generating API documentation...")

        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# API Endpoints Reference

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register/ | Register a new user |
| POST | /api/v1/auth/login/ | Login |
| POST | /api/v1/auth/token/refresh/ | Refresh access token |
| POST | /api/v1/auth/logout/ | Logout |
| GET | /api/v1/auth/profile/ | Get user profile |
| PUT | /api/v1/auth/profile/ | Update user profile |

## Destinations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/destinations/ | List all destinations |
| GET | /api/v1/destinations/{slug}/ | Get destination details |
| GET | /api/v1/destinations/{slug}/images/ | Get destination images |
| GET | /api/v1/destinations/{slug}/reviews/ | Get destination reviews |
| GET | /api/v1/destinations/{slug}/weather/ | Get destination weather |

## Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/search/autocomplete/ | Search autocomplete |
| GET | /api/v1/search/faceted/ | Faceted search |

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/health/ | Basic health check |
| GET | /api/v1/health/detailed/ | Detailed health check |

## Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/dashboard/stats/ | Admin dashboard statistics |
| GET | /api/v1/stats/ | Public statistics |
"""

        with open(docs_dir / "ENDPOINTS.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"API documentation generated at {docs_dir / 'ENDPOINTS.md'}"))
