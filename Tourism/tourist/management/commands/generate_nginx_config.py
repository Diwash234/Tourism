"""
Management command to generate an Nginx configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an Nginx configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating Nginx configuration...")

        content = """server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /app/media/;
    }

    location /ws/ {
        proxy_pass http://web:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""

        with open(Path("nginx.conf"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Nginx configuration generated at nginx.conf"))
