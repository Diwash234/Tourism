"""Admin CMS image management API.

Allows staff to search destinations by name and add/update/remove
images for destinations, hotels, and hospitals.

Endpoints:
    GET  /api/v1/admin/image-manager/search/?q=pokhara
    POST /api/v1/admin/image-manager/add/
    POST /api/v1/admin/image-manager/update/
    POST /api/v1/admin/image-manager/remove/
"""
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from tourist.models import Destination, DestinationImage, Hotel, Hospital


class Command(BaseCommand):
    help = "Admin CMS image management API."

    def handle(self, *args, **options):
        self.stdout.write("This module provides the admin image management API views.")
        self.stdout.write("Import from tourist.views_admin import AdminImageManagerView")
