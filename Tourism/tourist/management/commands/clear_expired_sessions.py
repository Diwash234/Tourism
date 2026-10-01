"""
Management command to clear expired sessions.
"""
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone


class Command(BaseCommand):
    help = "Clear expired sessions from the database"

    def handle(self, *args, **options):
        expired = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.stdout.write(self.style.SUCCESS(f"Cleared {count} expired sessions"))
