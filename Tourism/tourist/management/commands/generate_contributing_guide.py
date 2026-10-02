"""
Management command to generate a contributing guide.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a contributing guide"

    def handle(self, *args, **options):
        self.stdout.write("Generating contributing guide...")

        docs_dir = Path("docs")
        docs_dir.mkdir(parents=True, exist_ok=True)

        content = """# Contributing to Nepal Tourism Platform

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch
4. Make your changes
5. Submit a pull request

## Development Setup

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

## Code Style

- Follow PEP 8 for Python
- Use ESLint for JavaScript/React
- Write tests for new features
- Update documentation

## Pull Requests

- Keep PRs focused on a single feature
- Write clear commit messages
- Add tests for new functionality
- Update documentation as needed
"""

        with open(docs_dir / "CONTRIBUTING.md", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Contributing guide generated at {docs_dir / 'CONTRIBUTING.md'}"))
