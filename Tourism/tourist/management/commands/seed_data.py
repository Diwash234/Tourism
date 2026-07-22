from django.core.management.base import BaseCommand
from tourist.models import Language, Category, EmergencyContact, Destination


class Command(BaseCommand):
    help = "Seed reference data"

    def handle(self, *args, **options):

        # -------------------------
        # Languages
        # -------------------------
        languages = [
            ("en", "English"),
            ("ne", "Nepali"),
            ("hi", "Hindi"),
            ("fr", "French"),
            ("de", "German"),
            ("es", "Spanish"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("ru", "Russian"),
            ("ja", "Japanese"),
            ("ko", "Korean"),
            ("zh-cn", "Chinese (Simplified)"),
            ("zh-tw", "Chinese (Traditional)"),
            ("ar", "Arabic"),
            ("th", "Thai"),
            ("vi", "Vietnamese"),
            ("bn", "Bengali"),
            ("ur", "Urdu"),
            ("tr", "Turkish"),
            ("nl", "Dutch"),
            ("sv", "Swedish"),
            ("fi", "Finnish"),
            ("pl", "Polish"),
            ("cs", "Czech"),
            ("el", "Greek"),
            ("id", "Indonesian"),
            ("ms", "Malay"),
            ("fa", "Persian"),
        ]

        for code, name in languages:
            Language.objects.get_or_create(
                code=code,
                defaults={"name": name}
            )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(languages)} languages.")
        )

        # -------------------------
        # Categories
        # -------------------------
        categories = [
            {
                "name": "Heritage & Temples",
                "icon": "landmark",
                "description": "Ancient temples, UNESCO sites and historical monuments."
            },
            {
                "name": "Nature & Trekking",
                "icon": "mountain",
                "description": "National parks, trekking routes and mountains."
            },
            {
                "name": "Adventure Sports",
                "icon": "compass",
                "description": "Bungee, rafting, zipline, paragliding and more."
            },
            {
                "name": "Lakes & Water Activities",
                "icon": "water",
                "description": "Lakes, boating and water sports."
            },
            {
                "name": "Museums",
                "icon": "building",
                "description": "Museums showcasing history, culture and art."
            },
            {
                "name": "Food & Local Cuisine",
                "icon": "utensils",
                "description": "Traditional food, restaurants and local dishes."
            },
            {
                "name": "Religious Sites",
                "icon": "church",
                "description": "Temples, monasteries, churches and sacred places."
            },
            {
                "name": "Wildlife",
                "icon": "paw",
                "description": "Safari, jungle and wildlife reserves."
            },
            {
                "name": "National Parks",
                "icon": "tree",
                "description": "Protected forests and national parks."
            },
            {
                "name": "Camping",
                "icon": "campground",
                "description": "Camping and outdoor recreation."
            },
            {
                "name": "Photography Spots",
                "icon": "camera",
                "description": "Popular scenic viewpoints."
            },
            {
                "name": "Shopping",
                "icon": "shopping-bag",
                "description": "Markets and shopping centers."
            },
            {
                "name": "Festivals & Events",
                "icon": "calendar",
                "description": "Cultural festivals and celebrations."
            },
            {
                "name": "Mountain Peaks",
                "icon": "mountain",
                "description": "Major mountain summits."
            },
            {
                "name": "Waterfalls",
                "icon": "droplet",
                "description": "Natural waterfalls and cascades."
            },
        ]

        for cat in categories:
            Category.objects.get_or_create(
                name=cat["name"],
                defaults={
                    "icon": cat["icon"],
                    "description": cat["description"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(categories)} categories.")
        )

        # -------------------------
        # Emergency Contacts
        contacts = [

    # =========================
    # NATIONAL EMERGENCY
    # =========================

    {
        "contact_type": EmergencyContact.ContactType.POLICE,
        "name": "Nepal Police Emergency",
        "phone_number": "100",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7172,
        "longitude": 85.3240,
    },

    {
        "contact_type": EmergencyContact.ContactType.TOURISM_OFFICE,
        "name": "Nepal Tourist Police Hotline",
        "phone_number": "1144",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7172,
        "longitude": 85.3240,
    },

    {
        "contact_type": EmergencyContact.ContactType.FIRE_STATION,
        "name": "Nepal Fire Brigade Emergency",
        "phone_number": "101",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7172,
        "longitude": 85.3240,
    },

    {
        "contact_type": EmergencyContact.ContactType.AMBULANCE,
        "name": "Nepal Ambulance Emergency",
        "phone_number": "102",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7172,
        "longitude": 85.3240,
    },


    # =========================
    # KATHMANDU
    # =========================

    {
        "contact_type": EmergencyContact.ContactType.POLICE,
        "name": "Tourist Police Thamel",
        "phone_number": "+9779851289453",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7158,
        "longitude": 85.3119,
    },

    {
        "contact_type": EmergencyContact.ContactType.HOSPITAL,
        "name": "Bir Hospital Kathmandu",
        "phone_number": "+97714221988",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7046,
        "longitude": 85.3136,
    },

    {
        "contact_type": EmergencyContact.ContactType.HOSPITAL,
        "name": "Tribhuvan University Teaching Hospital",
        "phone_number": "+97714412600",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7351,
        "longitude": 85.3300,
    },

    {
        "contact_type": EmergencyContact.ContactType.TOURISM_OFFICE,
        "name": "Nepal Tourism Board",
        "phone_number": "+97714256909",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.6927,
        "longitude": 85.3188,
    },


    # =========================
    # POKHARA
    # =========================

    {
        "contact_type": EmergencyContact.ContactType.POLICE,
        "name": "Tourist Police Pokhara",
        "phone_number": "1144",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2096,
        "longitude": 83.9856,
    },

    {
        "contact_type": EmergencyContact.ContactType.HOSPITAL,
        "name": "Manipal Teaching Hospital Pokhara",
        "phone_number": "+97761526000",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2300,
        "longitude": 83.9950,
    },

    {
        "contact_type": EmergencyContact.ContactType.HOSPITAL,
        "name": "Western Regional Hospital Pokhara",
        "phone_number": "+97761520067",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2380,
        "longitude": 83.9956,
    },

    {
        "contact_type": EmergencyContact.ContactType.TOURISM_OFFICE,
        "name": "Pokhara Tourism Office",
        "phone_number": "+97761531002",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2096,
        "longitude": 83.9856,
    },


    # =========================
    # CHITWAN
    # =========================

    {
        "contact_type": EmergencyContact.ContactType.POLICE,
        "name": "Tourist Police Sauraha Chitwan",
        "phone_number": "1144",
        "city": "Sauraha",
        "country": "Nepal",
        "latitude": 27.5800,
        "longitude": 84.4900,
    },

    {
        "contact_type": EmergencyContact.ContactType.HOSPITAL,
        "name": "Bharatpur Hospital",
        "phone_number": "+97756527000",
        "city": "Bharatpur",
        "country": "Nepal",
        "latitude": 27.6766,
        "longitude": 84.4304,
    },


    # =========================
    # LUMBINI
    # =========================

    {
        "contact_type": EmergencyContact.ContactType.POLICE,
        "name": "Lumbini Tourist Police",
        "phone_number": "1144",
        "city": "Lumbini",
        "country": "Nepal",
        "latitude": 27.4833,
        "longitude": 83.2767,
    },

    {
        "contact_type": EmergencyContact.ContactType.HOSPITAL,
        "name": "Lumbini Provincial Hospital",
        "phone_number": "+97771520011",
        "city": "Lumbini",
        "country": "Nepal",
        "latitude": 27.5000,
        "longitude": 83.2800,
    },


    # =========================
    # EVEREST REGION
    # =========================

    {
        "contact_type": EmergencyContact.ContactType.AMBULANCE,
        "name": "Lukla Emergency Rescue",
        "phone_number": "102",
        "city": "Lukla",
        "country": "Nepal",
        "latitude": 27.6878,
        "longitude": 86.7314,
    },

]
        destinations = [
            {
                "name": "Phewa Lake",
                "category": "Lakes & Water Activities",
                "description": "A beautiful freshwater lake in Pokhara famous for boating and mountain views.",
                "latitude": 28.2096,
                "longitude": 83.9856,
                "city": "Pokhara",
                "country": "Nepal",
                "entry_fee": 0,
            },
            {
                "name": "Sarangkot",
                "category": "Nature & Trekking",
                "description": "A famous viewpoint for sunrise and Himalayan mountain views.",
                "latitude": 28.2498,
                "longitude": 83.9442,
                "city": "Pokhara",
                "country": "Nepal",
                "entry_fee": 50,
            },
            {
                "name": "World Peace Pagoda",
                "category": "Heritage & Temples",
                "description": "A Buddhist stupa overlooking Pokhara valley and Phewa Lake.",
                "latitude": 28.2036,
                "longitude": 83.9485,
                "city": "Pokhara",
                "country": "Nepal",
                "entry_fee": 0,
            },
            {
                "name": "International Mountain Museum",
                "category": "Museums",
                "description": "Museum showcasing Himalayan culture, history and mountaineering.",
                "latitude": 28.1920,
                "longitude": 84.0008,
                "city": "Pokhara",
                "country": "Nepal",
                "entry_fee": 500,
            },
        ]

        for item in destinations:
            category = Category.objects.get(name=item["category"])
            Destination.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": category,
                    "description": item["description"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "city": item["city"],
                    "country": item["country"],
                    "entry_fee": item["entry_fee"],
                    "status": Destination.SubmissionStatus.APPROVED,
                    "is_active": True,
                    "is_user_submitted": False,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(destinations)} destinations.")
        )