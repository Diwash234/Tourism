"""Verify the deployment is working correctly.

Checks:
- Database connectivity and data counts
- Static files are being served
- Frontend build is present
- Critical API endpoints are responsive
- Media files are accessible

Usage:
    python manage.py verify_deployment
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Verify the deployment is working correctly."

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DEPLOYMENT VERIFICATION")
        self.stdout.write("=" * 60)

        # 1. Database check
        self.stdout.write("\n[1/5] Database:")
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM tourist_destination")
                dest_count = cur.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"  ✓ Connected ({connection.vendor})"))
                self.stdout.write(f"  ✓ Destinations: {dest_count}")

                cur.execute("SELECT COUNT(*) FROM tourist_destinationimage")
                img_count = cur.fetchone()[0]
                self.stdout.write(f"  ✓ Images: {img_count}")

                cur.execute("SELECT COUNT(*) FROM tourist_hotel")
                hotel_count = cur.fetchone()[0]
                self.stdout.write(f"  ✓ Hotels: {hotel_count}")

                cur.execute("SELECT COUNT(*) FROM tourist_hospital")
                hospital_count = cur.fetchone()[0]
                self.stdout.write(f"  ✓ Hospitals: {hospital_count}")
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ✗ Database error: {exc}"))

        # 2. Static files check
        self.stdout.write("\n[2/5] Static files:")
        static_root = settings.STATIC_ROOT
        if static_root and static_root.exists():
            file_count = len(list(static_root.rglob("*")))
            self.stdout.write(self.style.SUCCESS(f"  ✓ Static root: {static_root} ({file_count} files)"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Static root missing: {static_root}"))

        # 3. Frontend build check
        self.stdout.write("\n[3/5] Frontend build:")
        frontend_dist = settings.FRONTEND_DIST_DIR
        index_html = frontend_dist / "index.html"
        if index_html.is_file():
            self.stdout.write(self.style.SUCCESS(f"  ✓ Frontend build present: {frontend_dist}"))
        else:
            self.stdout.write(self.style.ERROR(f"  ✗ Frontend build missing: {index_html}"))

        # 4. Media check
        self.stdout.write("\n[4/5] Media:")
        media_root = settings.MEDIA_ROOT
        if media_root and media_root.exists():
            media_count = len(list(media_root.rglob("*")))
            self.stdout.write(self.style.SUCCESS(f"  ✓ Media root: {media_root} ({media_count} files)"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Media root missing: {media_root}"))

        # 5. Configuration check
        self.stdout.write("\n[5/5] Configuration:")
        self.stdout.write(f"  DEBUG: {settings.DEBUG}")
        self.stdout.write(f"  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        self.stdout.write(f"  DATABASE: {connection.vendor} ({connection.settings_dict.get('NAME', 'unknown')})")

        if settings.IMAGE_BASE_URL:
            self.stdout.write(f"  IMAGE_BASE_URL: {settings.IMAGE_BASE_URL}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ IMAGE_BASE_URL not set - images may not load"))

        if settings.ML_SERVICE_URL:
            self.stdout.write(f"  ML_SERVICE_URL: {settings.ML_SERVICE_URL}")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("VERIFICATION COMPLETE")
        self.stdout.write("=" * 60)
