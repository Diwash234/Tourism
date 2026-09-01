"""Idempotent demo users and marketplace offers for Playwright feature e2e."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from tourist.location_sync import apply_destination_locations
from tourist.models import MarketplaceListing, MarketplacePartner, User


class Command(BaseCommand):
    help = "Ensure demo logins and published marketplace packages exist for e2e."

    def handle(self, *args, **options):
        applied = apply_destination_locations()
        if applied:
            self.stdout.write(f"Applied {applied} recorded destination locations from JSON.")
        users = [
            {
                "email": "admin@tourism.gov.np",
                "password": "Admin@12345",
                "first_name": "Nepal",
                "last_name": "Admin",
                "role": User.Role.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "staff@tourism.gov.np",
                "password": "Staff@12345",
                "first_name": "Tourism",
                "last_name": "Staff",
                "role": User.Role.STAFF,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "tourist@nepaltourism.com",
                "password": "Tourist@12345",
                "first_name": "Namaste",
                "last_name": "Traveler",
                "role": User.Role.TOURIST,
                "is_staff": False,
                "is_superuser": False,
            },
        ]
        for spec in users:
            password = spec.pop("password")
            email = spec["email"]
            user, created = User.objects.get_or_create(email=email, defaults={
                **spec,
                "is_active": True,
                "is_verified": True,
            })
            if not created:
                for key, value in spec.items():
                    setattr(user, key, value)
            user.is_active = True
            user.is_verified = True
            user.set_password(password)
            user.save()

        tourist = User.objects.get(email="tourist@nepaltourism.com")
        partner, _ = MarketplacePartner.objects.update_or_create(
            email="tourist@nepaltourism.com",
            defaults={
                "name": "E2E Himalayan Desk",
                "kind": MarketplacePartner.Kind.OPERATOR,
                "status": MarketplacePartner.Status.APPROVED,
                "user": tourist,
                "city": "Pokhara",
                "district": "Kaski",
                "website": "https://example.com",
                "contact_name": "E2E Partner",
                "description": "Approved partner used by Playwright feature tests.",
            },
        )

        offers = [
            {
                "slug": "e2e-five-day-nepal-circuit",
                "title": "E2E Five Day Nepal Circuit",
                "summary": "Published five-day Pokhara circuit used by Playwright.",
                "description": "Kathmandu arrival and Pokhara lakeside days.",
                "includes": "Guide\nLodge breakfast",
                "duration_days": 5,
                "price_npr": Decimal("45000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
            },
            {
                "slug": "e2e-six-day-alternative",
                "title": "E2E Six Day Alternative Circuit",
                "summary": "Nearby-duration published alternative under $500.",
                "description": "One extra day around Phewa.",
                "includes": "Guide",
                "duration_days": 6,
                "price_npr": Decimal("50000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": False,
            },
            {
                "slug": "e2e-over-budget-week",
                "title": "E2E Luxury Over Budget Week",
                "summary": "Same duration but over a $500 budget.",
                "description": "Should never appear as a $500 match.",
                "includes": "Luxury lodge",
                "duration_days": 5,
                "price_npr": Decimal("250000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": False,
            },
            {
                "slug": "e2e-pending-hidden-stay",
                "title": "E2E Hidden Pending Stay",
                "summary": "Must stay off the public catalogue.",
                "description": "Pending partner offer.",
                "includes": "",
                "duration_days": 2,
                "price_npr": Decimal("1000.00"),
                "status": MarketplaceListing.Status.PENDING,
                "is_featured": False,
            },
        ]
        for row in offers:
            MarketplaceListing.objects.update_or_create(
                slug=row["slug"],
                defaults={
                    "partner": partner,
                    "kind": MarketplaceListing.Kind.PACKAGE,
                    "title": row["title"],
                    "summary": row["summary"],
                    "description": row["description"],
                    "includes": row["includes"],
                    "duration_days": row["duration_days"],
                    "price_npr": row["price_npr"],
                    "city": "Pokhara",
                    "district": "Kaski",
                    "status": row["status"],
                    "is_featured": row["is_featured"],
                    "image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80",
                },
            )

        self.stdout.write(self.style.SUCCESS(
            "E2E users and marketplace packages are ready."
        ))
