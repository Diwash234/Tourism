from django.core.management.base import BaseCommand

from tourist.models import Language, Category, EmergencyContact


class Command(BaseCommand):
    help = "Seeds baseline reference data: languages, categories, and sample emergency contacts."

    def handle(self, *args, **options):
        languages = [
            ("en", "English"), ("ne", "Nepali"), ("hi", "Hindi"),
            ("fr", "French"), ("de", "German"), ("zh-cn", "Chinese (Simplified)"),
            ("ja", "Japanese"), ("es", "Spanish"),
        ]
        for code, name in languages:
            Language.objects.get_or_create(code=code, defaults={"name": name})
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(languages)} languages."))

        categories = [
            ("Heritage & Temples", "landmark"),
            ("Nature & Trekking", "mountain"),
            ("Lakes & Water Activities", "water"),
            ("Adventure Sports", "compass"),
            ("Museums", "building"),
            ("Food & Local Cuisine", "utensils"),
        ]
        for name, icon in categories:
            Category.objects.get_or_create(name=name, defaults={"icon": icon})
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(categories)} categories."))

        contacts = [
            {
                "contact_type": EmergencyContact.ContactType.POLICE,
                "name": "Pokhara Tourist Police",
                "phone_number": "+9779800000000",
                "city": "Pokhara", "country": "Nepal",
                "latitude": 28.2096, "longitude": 83.9856,
            },
            {
                "contact_type": EmergencyContact.ContactType.HOSPITAL,
                "name": "Western Regional Hospital",
                "phone_number": "+9779800000001",
                "city": "Pokhara", "country": "Nepal",
                "latitude": 28.2380, "longitude": 83.9956,
            },
            {
                "contact_type": EmergencyContact.ContactType.TOURISM_OFFICE,
                "name": "Nepal Tourism Board - Pokhara",
                "phone_number": "+9779800000002",
                "city": "Pokhara", "country": "Nepal",
                "latitude": 28.2100, "longitude": 83.9800,
            },
            {
                "contact_type": EmergencyContact.ContactType.FIRE_STATION,
                "name": "Pokhara Fire Brigade",
                "phone_number": "+9779800000003",
                "city": "Pokhara", "country": "Nepal",
                "latitude": 28.2200, "longitude": 83.9900,
            },
        ]
        for c in contacts:
            EmergencyContact.objects.get_or_create(name=c["name"], defaults=c)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(contacts)} emergency contacts."))

        self.stdout.write(self.style.SUCCESS("Seed data complete."))