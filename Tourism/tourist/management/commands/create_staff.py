"""
Create a staff account from the command line.

Staff accounts (moderators, district managers, hotel managers, tourist
police) are NOT created via the public sign-up form -- that form only ever
creates tourist accounts. This command lets an administrator provision a
staff account securely from the backend, mirroring how superusers are
created with `python manage.py createsuperuser`.

Usage:
    python manage.py create_staff --email staff@tourism.gov.np \\
        --first-name Staff --last-name Member --role staff

Roles match the User.Role choices (tourist/models.py):
    staff, content_moderator, district_manager, hotel_manager,
    tourist_police, guide, ...
"""
import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create a staff account (staff cannot self-register on the public site)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")
        parser.add_argument("--role", default="staff", help="User.Role value, e.g. staff, content_moderator, district_manager")
        parser.add_argument("--password", default=None, help="If omitted, you'll be prompted securely.")
        parser.add_argument("--managed-district", default="", help="For district_manager role.")
        parser.add_argument("--superuser", action="store_true", help="Also grant superuser (full admin).")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email {email} already exists.")

        valid_roles = {c[0] for c in User.Role.choices}
        role = options["role"].strip().lower()
        if role not in valid_roles:
            raise CommandError(f"Invalid role '{role}'. Choices: {', '.join(sorted(valid_roles))}")

        password = options["password"]
        if not password:
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                raise CommandError("Passwords did not match.")
        if len(password) < 6:
            raise CommandError("Password must be at least 6 characters.")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=options["first_name"],
            last_name=options["last_name"],
            role=role,
            is_staff=True,
            is_verified=True,
            is_superuser=options["superuser"],
            managed_district=options["managed_district"],
        )
        self.stdout.write(self.style.SUCCESS(
            f"Created {'superuser' if options['superuser'] else 'staff'} account: {email} (role={role})"
        ))
