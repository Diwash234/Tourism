"""
Management command to generate API documentation.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate API documentation"

    def handle(self, *args, **options):
        self.stdout.write("Generating API documentation...")

        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Generate a basic API documentation file
        content = """# Nepal Tourism Platform API Documentation

## Base URL
```
https://your-domain.com/api/v1/
```

## Authentication
All API endpoints require JWT authentication via the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Auth
- POST /auth/register/ - Register a new user
- POST /auth/login/ - Login
- POST /auth/token/refresh/ - Refresh access token
- POST /auth/logout/ - Logout

### Destinations
- GET /destinations/ - List all destinations
- GET /destinations/{slug}/ - Get destination details
- GET /destinations/{slug}/images/ - Get destination images

### Search
- GET /search/autocomplete/?q={query} - Autocomplete suggestions
- GET /search/faceted/?q={query} - Faceted search

### Health
- GET /health/ - Basic health check
- GET /health/detailed/ - Detailed health check

## Response Format
```json
{
  "success": true,
  "data": {},
  "message": "Success"
}
```

## Error Format
```json
{
  "success": false,
  "error": {
    "code": "error_code",
    "message": "Error message",
    "details": {}
  }
}
```
"""

        with open(docs_dir / "README.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"API documentation generated at {docs_dir / 'README.md'}"))
