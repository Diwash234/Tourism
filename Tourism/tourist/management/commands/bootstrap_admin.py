import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create or repair the primary Tourism administrator account without touching other users."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=os.getenv("TOURISM_ADMIN_EMAIL", "admin123@gmail.com"))
        parser.add_argument("--password", default=os.getenv("TOURISM_ADMIN_PASSWORD"))

    def handle(self, *args, **options):
        User = get_user_model()
        email = (options["email"] or "").strip().lower()
        password = options["password"]

        if not email:
            raise CommandError("TOURISM_ADMIN_EMAIL must not be empty.")
        if not password:
            raise CommandError("TOURISM_ADMIN_PASSWORD must be set before bootstrapping the admin account.")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Tourism",
                "last_name": "Administrator",
                "role": "super_admin",
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
                "is_active": True,
            },
        )

        # Idempotent repair: only the explicitly selected admin account is
        # promoted/repaired; no existing users or tourism data are deleted.
        user.first_name = user.first_name or "Tourism"
        user.last_name = user.last_name or "Administrator"
        user.role = "super_admin"
        user.is_staff = True
        user.is_superuser = True
        user.is_verified = True
        user.is_active = True
        user.set_password(password)
        user.save(update_fields=[
            "first_name",
            "last_name",
            "role",
            "is_staff",
            "is_superuser",
            "is_verified",
            "is_active",
            "password",
        ])

        action = "created" if created else "repaired"
        self.stdout.write(self.style.SUCCESS(
            f"Primary administrator {action}: {email} (role=super_admin)"
        ))
