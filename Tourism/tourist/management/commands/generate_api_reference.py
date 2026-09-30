"""
Management command to generate an API reference document.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an API reference document"

    def handle(self, *args, **options):
        self.stdout.write("Generating API reference...")

        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Nepal Tourism Platform API Reference

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
- GET /auth/profile/ - Get user profile
- PUT /auth/profile/ - Update user profile

### Destinations
- GET /destinations/ - List all destinations
- GET /destinations/{slug}/ - Get destination details
- GET /destinations/{slug}/images/ - Get destination images
- GET /destinations/{slug}/reviews/ - Get destination reviews
- GET /destinations/{slug}/weather/ - Get destination weather

### Search
- GET /search/autocomplete/?q={query} - Autocomplete suggestions
- GET /search/faceted/?q={query} - Faceted search

### Health
- GET /health/ - Basic health check
- GET /health/detailed/ - Detailed health check

### Dashboard
- GET /dashboard/stats/ - Admin dashboard statistics
- GET /stats/ - Public statistics

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

## Rate Limiting
- Auth endpoints: 10 requests per minute
- General API: 60 requests per minute
- Search: 30 requests per minute
"""

        with open(docs_dir / "REFERENCE.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"API reference generated at {docs_dir / 'REFERENCE.md'}"))
