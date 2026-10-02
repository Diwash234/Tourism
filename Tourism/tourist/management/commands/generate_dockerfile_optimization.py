"""
Management command to generate an optimized Dockerfile.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an optimized Dockerfile"

    def handle(self, *args, **options):
        self.stdout.write("Generating optimized Dockerfile...")

        content = """# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY Tourism/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5 \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY Tourism/ /app/Tourism/
WORKDIR /app/Tourism

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "Tourism.wsgi:application"]
"""

        with open(Path("Dockerfile.optimized"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Optimized Dockerfile generated at Dockerfile.optimized"))
