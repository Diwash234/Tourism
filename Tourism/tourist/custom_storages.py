"""
Custom storage backends for the Tourism platform.
"""
import os

from django.core.files.storage import FileSystemStorage
from django.conf import settings


class MediaStorage(FileSystemStorage):
    """Custom media storage with organized directory structure."""

    def __init__(self, location=None, base_url=None):
        location = location or settings.MEDIA_ROOT
        base_url = base_url or settings.MEDIA_URL
        super().__init__(location, base_url)

    def get_available_name(self, name, max_length=None):
        """Organize uploads by date."""
        import datetime
        now = datetime.datetime.now()
        date_path = now.strftime("%Y/%m")
        name = os.path.join(date_path, name)
        return super().get_available_name(name, max_length)


class ImageStorage(FileSystemStorage):
    """Custom image storage with validation."""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    def get_valid_name(self, name):
        """Validate image extension."""
        ext = os.path.splitext(name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid image extension: {ext}")
        return name
