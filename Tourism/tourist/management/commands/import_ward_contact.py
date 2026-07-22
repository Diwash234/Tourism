"""
Imports local ward office/ward member contacts (name, designation, ward
number, phone) into the EmergencyContact table.

Expected CSV columns:
    name, designation, ward_number, phone_number, alternate_phone,
    address, city, country, latitude, longitude

Usage:
    python manage.py import_ward_contacts path/to/ward_contacts.csv
"""
import csv

from django.core.management.base import BaseCommand, CommandError

from tourist.models import EmergencyContact


class Command(BaseCommand):
    help = "Imports local ward office/ward member contacts into the EmergencyContact table."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        created, updated = 0, 0

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    designation = row.get("designation", "").strip()
                    contact_type = (
                        EmergencyContact.ContactType.WARD_OFFICE
                        if "office" in designation.lower()
                        else EmergencyContact.ContactType.WARD_MEMBER
                    )
                    _, was_created = EmergencyContact.objects.update_or_create(
                        name=row["name"].strip(),
                        ward_number=row.get("ward_number") or None,
                        defaults={
                            "contact_type": contact_type,
                            "designation": designation,
                            "phone_number": row["phone_number"].strip(),
                            "alternate_phone": row.get("alternate_phone", "").strip() or None,
                            "address": row.get("address", "").strip(),
                            "city": row.get("city", "").strip(),
                            "country": row.get("country", "Nepal").strip(),
                            "latitude": row["latitude"],
                            "longitude": row["longitude"],
                        },
                    )
                    created += was_created
                    updated += not was_created
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")
        except KeyError as exc:
            raise CommandError(f"Missing required column in CSV: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Ward contacts: {created} created, {updated} updated."))
