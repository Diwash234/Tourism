"""Seed the staff-ops demo user used by the live e2e suite and manual checks.

    python manage.py seed_staff_demo

Idempotent: safe to re-run after restoring db.sqlite3 from git. Creates
staff-ops@nepaltourism.com (role staff) with the capability profile the live
e2e expects, assigns one active hotel, and creates two probe bookings when
none exist yet.
"""
import datetime

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the staff-ops demo user, capabilities, hotel assignment and probe bookings."

    def handle(self, *args, **options):
        from tourist.models import Hotel, StaffCapabilityProfile, User
        from admin_panel.models import HotelAssignment
        from booking.models import Booking

        user, created = User.objects.get_or_create(
            email="staff-ops@nepaltourism.com",
            defaults={"first_name": "Staff", "last_name": "Ops", "role": "staff", "is_staff": True},
        )
        if created:
            user.set_password("StaffOps!12345")
        user.role = "staff"
        user.is_staff = True
        user.save()

        profile, _ = StaffCapabilityProfile.objects.get_or_create(user=user)
        caps = profile.capabilities or {}
        caps["feedback"] = ["view", "change"]
        caps["hotels"] = ["view", "change"]
        caps["destinations"] = ["view", "add", "change"]
        caps["images"] = ["view", "add"]
        caps["safety"] = ["view", "change"]
        caps["marketplace"] = ["view", "add", "change"]
        profile.capabilities = caps
        profile.save()

        hotel = Hotel.objects.filter(is_active=True).first()
        if hotel:
            HotelAssignment.objects.get_or_create(hotel=hotel, admin=user)

        tourist = User.objects.filter(email="tourist@nepaltourism.com").first()
        if hotel and tourist and not Booking.objects.filter(hotel=hotel, user=tourist).exists():
            Booking.objects.create(
                user=tourist, hotel=hotel,
                check_in=datetime.date.today() + datetime.timedelta(days=30),
                check_out=datetime.date.today() + datetime.timedelta(days=33),
                guests=2, special_requests="Live e2e probe booking",
            )
            other = Hotel.objects.exclude(id=hotel.id).first()
            if other:
                Booking.objects.create(
                    user=tourist, hotel=other,
                    check_in=datetime.date.today() + datetime.timedelta(days=30),
                    check_out=datetime.date.today() + datetime.timedelta(days=31),
                    guests=1,
                )
        self.stdout.write(self.style.SUCCESS(
            f"staff-ops seeded (created={created}); hotel={'yes' if hotel else 'none'}"
        ))
