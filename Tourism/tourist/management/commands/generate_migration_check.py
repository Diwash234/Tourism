"""
Management command to check for pending migrations.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check for pending migrations"

    def handle(self, *args, **options):
        self.stdout.write("Checking for pending migrations...")

        try:
            call_command("makemigrations", "--check", "--dry-run")
            self.stdout.write(self.style.SUCCESS("No pending migrations"))
        except SystemExit:
            self.stdout.write(self.style.WARNING("Pending migrations detected"))
            self.stdout.write("\nRun 'python manage.py migrate' to apply them")
