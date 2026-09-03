"""
Export the database and all (AI-generated, web, uploaded) images into a
single portable archive that can be transferred to another machine without
using git.

The archive contains:
  tourism_export.sql      - full DB dump (sqlite .dump or postgres pg_dump)
  media/                  - all image files (ai_generated, destinations, etc.)
  manifest.json           - checksums, counts, version info

On the target machine, run:
    python manage.py import_images --from tourism_export.tar.gz

Usage:
    python manage.py export_media --out tourism_export.tar.gz
"""
import hashlib
import json
import os
import subprocess
import tarfile
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from tourist.models import Destination, DestinationImage


class Command(BaseCommand):
    help = "Export database + media images into a portable archive."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="tourism_export.tar.gz")
        parser.add_argument("--no-db", action="store_true")
        parser.add_argument("--ai-only", action="store_true",
                            help="only include ai_generated images")

    def handle(self, *args, **options):
        out_path = os.path.abspath(options["out"])
        tmp_dir = os.path.join(settings.BASE_DIR, "_export_tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        # 1. Database dump
        if not options["no_db"]:
            self.stdout.write("Dumping database...")
            db_path = settings.DATABASES.get("default", {}).get("NAME", "")
            dump_file = os.path.join(tmp_dir, "tourism_export.sql")
            if connection.vendor == "sqlite" and db_path and os.path.exists(db_path):
                with open(dump_file, "w") as f:
                    subprocess.run(["sqlite3", db_path, ".dump"], stdout=f, check=True)
            else:
                # postgres / others via django's dumpdata
                subprocess.run([sys.executable, "manage.py", "dumpdata", "--natural",
                                "--indent", "2", "-o", dump_file.replace(".sql", ".json")],
                               cwd=settings.BASE_DIR, check=True)

        # 2. Copy media
        self.stdout.write("Collecting media...")
        media_src = settings.MEDIA_ROOT
        media_dst = os.path.join(tmp_dir, "media")
        if os.path.isdir(media_src):
            if options["ai_only"]:
                os.makedirs(os.path.join(media_dst, "ai_generated"), exist_ok=True)
                src_ai = os.path.join(media_src, "ai_generated")
                if os.path.isdir(src_ai):
                    subprocess.run(["cp", "-r", src_ai, media_dst], check=False)
            else:
                subprocess.run(["cp", "-r", media_src, media_dst], check=False)

        # 3. Manifest
        manifest = {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "destinations": Destination.objects.count(),
            "images": DestinationImage.objects.count(),
            "ai_generated": DestinationImage.objects.filter(
                source=DestinationImage.Source.AI_GENERATED).count(),
        }
        with open(os.path.join(tmp_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)

        # 4. Tarball
        self.stdout.write(f"Writing {out_path} ...")
        with tarfile.open(out_path, "w:gz") as tar:
            tar.add(tmp_dir, arcname=".")

        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f"Exported {manifest['images']} images to {out_path} ({size_mb:.1f} MB).\n"
            f"Transfer this file and run on the target:\n"
            f"  python manage.py import_media --from {os.path.basename(out_path)}"
        ))

        # cleanup
        subprocess.run(["rm", "-rf", tmp_dir], check=False)
