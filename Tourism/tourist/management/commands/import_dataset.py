"""
Imports a tourism dataset CSV into the Destination/Category tables so
Django becomes the single source of truth (frontend reads from here, and
the ML service can pull a fresh export from here too — see
tourist/management/commands/export_dataset.py).

Expected CSV columns (rename/adjust to match your actual dataset):
    name, category, description, latitude, longitude, city, country,
    entry_fee, average_rating

Usage:
    python manage.py import_dataset path/to/tourism_dataset.csv
"""
import csv

from django.core.management.base import BaseCommand, CommandError

from tourist.models import Category, Destination, User


class Command(BaseCommand):
    help = "Imports a tourism dataset CSV into the Destination table."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument(
            "--owner-email",
            type=str,
            default=None,
            help="Email of an existing admin user to set as created_by (optional).",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        owner = None
        if options["owner_email"]:
            try:
                owner = User.objects.get(email=options["owner_email"])
            except User.DoesNotExist:
                raise CommandError(f"No user with email {options['owner_email']}")

        created, skipped = 0, 0
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category, _ = Category.objects.get_or_create(name=row["category"].strip())

                    if Destination.objects.filter(name=row["name"].strip()).exists():
                        skipped += 1
                        continue

                    Destination.objects.create(
                        name=row["name"].strip(),
                        category=category,
                        description=row.get("description", "").strip(),
                        latitude=row["latitude"],
                        longitude=row["longitude"],
                        city=row.get("city", "").strip(),
                        country=row.get("country", "").strip(),
                        entry_fee=row.get("entry_fee") or 0,
                        average_rating=row.get("average_rating") or 0,
                        created_by=owner,
                        is_user_submitted=False,
                        status=Destination.SubmissionStatus.APPROVED,
                    )
                    created += 1
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")
        except KeyError as exc:
            raise CommandError(f"Missing required column in CSV: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Imported {created} destinations, skipped {skipped} duplicates."))
