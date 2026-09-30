"""
Management command to generate a README file.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a README file"

    def handle(self, *args, **options):
        self.stdout.write("Generating README...")

        content = """# Nepal Tourism Platform

An autonomous, AI-driven, multi-modal travel recommendation, real-time safety, navigation, and budget estimation platform for Nepal.

## Features

- Destination discovery and search
- AI-powered recommendations
- Real-time safety alerts
- Navigation and routing
- Budget estimation
- Multi-language support
- User reviews and ratings
- Travel planning
- Emergency services

## Quick Start

```bash
# Backend
cd Tourism
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend/Tourism
npm install
npm run dev
```

## API Documentation

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## License

MIT License
"""

        with open(Path("README_GENERATED.md"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("README generated at README_GENERATED.md"))
