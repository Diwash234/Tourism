"""
Management command to generate GitHub Actions workflow.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate GitHub Actions workflow"

    def handle(self, *args, **options):
        self.stdout.write("Generating GitHub Actions workflow...")

        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)

        content = """name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r Tourism/requirements.txt
      - name: Run tests
        working-directory: Tourism
        run: |
          python manage.py test --noinput

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t tourism-platform .
"""

        with open(workflow_dir / "ci.yml", "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f"GitHub Actions workflow generated at {workflow_dir / 'ci.yml'}"))
