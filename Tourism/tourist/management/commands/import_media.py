"""
Import a previously exported database + media archive produced by
``export_media``.

Usage:
    python manage.py import_media --from tourism_export.tar.gz
"""
import json
import os
import shutil
import subprocess
import tarfile
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Import database dump + media from an export archive."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="archive", required=True)
        parser.add_argument("--no-db", action="store_true")
        parser.add_argument("--yes", action="store_true",
                            help="overwrite existing media without prompting")

    def handle(self, *args, **options):
        archive = os.path.abspath(options["archive"])
        if not os.path.exists(archive):
            raise FileNotFoundError(archive)

        tmp = tempfile.mkdtemp(prefix="tourism_import_")
        self.stdout.write(f"Extracting {archive} ...")
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(tmp)

        # 1. Database
        if not options["no_db"]:
            self.stdout.write("Importing database...")
            sql = os.path.join(tmp, "tourism_export.sql")
            json_dump = os.path.join(tmp, "tourism_export.json")
            db_path = settings.DATABASES.get("default", {}).get("NAME", "")
            if os.path.exists(sql) and connection.vendor == "sqlite":
                # backup current DB
                if os.path.exists(db_path) and not options["yes"]:
                    shutil.copy(db_path, db_path + ".bak")
                subprocess.run(["sqlite3", db_path, f".read {sql}"], check=True)
            elif os.path.exists(json_dump):
                call_command("loaddata", json_dump)

        # 2. Media files
        media_src = os.path.join(tmp, "media")
        if os.path.isdir(media_src):
            self.stdout.write("Copying media files...")
            media_dst = settings.MEDIA_ROOT
            os.makedirs(media_dst, exist_ok=True)
            for item in os.listdir(media_src):
                s = os.path.join(media_src, item)
                d = os.path.join(media_dst, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

        manifest = os.path.join(tmp, "manifest.json")
        if os.path.exists(manifest):
            with open(manifest) as f:
                m = json.load(f)
            self.stdout.write(self.style.SUCCESS(
                f"Import complete: {m.get('destinations')} destinations, "
                f"{m.get('images')} images ({m.get('ai_generated')} AI)."
            ))

        shutil.rmtree(tmp, ignore_errors=True)
