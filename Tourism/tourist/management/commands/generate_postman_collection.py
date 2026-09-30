"""
Management command to generate a Postman collection.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Postman collection"

    def handle(self, *args, **options):
        self.stdout.write("Generating Postman collection...")

        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)

        collection = {
            "info": {
                "name": "Nepal Tourism Platform API",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [
                {
                    "name": "Auth",
                    "item": [
                        {
                            "name": "Register",
                            "request": {
                                "method": "POST",
                                "header": [{"key": "Content-Type", "value": "application/json"}],
                                "url": "{{base_url}}/auth/register/",
                                "body": {
                                    "mode": "raw",
                                    "raw": '{\n  "email": "user@example.com",\n  "password": "password123",\n  "first_name": "John",\n  "last_name": "Doe"\n}',
                                },
                            },
                        },
                        {
                            "name": "Login",
                            "request": {
                                "method": "POST",
                                "header": [{"key": "Content-Type", "value": "application/json"}],
                                "url": "{{base_url}}/auth/login/",
                                "body": {
                                    "mode": "raw",
                                    "raw": '{\n  "email": "user@example.com",\n  "password": "password123"\n}',
                                },
                            },
                        },
                    ],
                },
                {
                    "name": "Destinations",
                    "item": [
                        {
                            "name": "List Destinations",
                            "request": {
                                "method": "GET",
                                "url": "{{base_url}}/destinations/",
                            },
                        },
                        {
                            "name": "Get Destination",
                            "request": {
                                "method": "GET",
                                "url": "{{base_url}}/destinations/pokhara/",
                            },
                        },
                    ],
                },
            ],
            "variable": [
                {"key": "base_url", "value": "https://your-domain.com/api/v1"},
            ],
        }

        with open(docs_dir / "postman_collection.json", "w") as f:
            json.dump(collection, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Postman collection generated at {docs_dir / 'postman_collection.json'}"))
