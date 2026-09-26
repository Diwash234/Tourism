"""Verify that a SQLite database and canonical JSON contain the same safe data."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from tourist.models import Destination, SiteSetting, User
from tourist.verified_snapshot import (
    FORBIDDEN_RUNTIME_LABELS,
    as_of_from_payload,
    build_snapshot_payload,
    read_payload,
)


class Command(BaseCommand):
    help = "Verify JSON/database record equality, privacy gates, migrations, and SQLite integrity."

    def add_arguments(self, parser):
        parser.add_argument("input", help="Canonical verified tourism JSON path.")
        parser.add_argument(
            "--database",
            default="",
            help="Optional SQLite path. Defaults to the active Django database.",
        )
        parser.add_argument("--internal", action="store_true", help=argparse.SUPPRESS)

    def handle(self, *args, **options):
        input_path = Path(options["input"])
        database = options.get("database")
        if database and not options.get("internal"):
            target = Path(database).resolve()
            active = Path(connection.settings_dict["NAME"]).resolve()
            if target != active:
                env = os.environ.copy()
                env["DB_NAME"] = str(target)
                env["DB_ENGINE"] = "sqlite"
                env["DATABASE_URL"] = ""
                env["PYTHONDONTWRITEBYTECODE"] = "1"
                command = [
                    sys.executable,
                    str(Path(settings.BASE_DIR) / "manage.py"),
                    "verify_verified_snapshot",
                    str(input_path),
                    "--internal",
                ]
                subprocess.run(command, cwd=settings.BASE_DIR, env=env, check=True)
                return

        payload = read_payload(input_path)
        actual = build_snapshot_payload(as_of=as_of_from_payload(payload))
        if actual["records_sha256"] != payload["records_sha256"]:
            # Normalize Python Decimal/date values through Django's JSON
            # encoder before producing a useful field-level diff.  A freshly
            # loaded DB naturally returns model types while the on-disk JSON
            # contains strings for those scalar values.
            from django.core.serializers.json import DjangoJSONEncoder
            actual_records = json.loads(json.dumps(
                actual["records"],
                cls=DjangoJSONEncoder,
                sort_keys=True,
            ))
            expected_by_key = {(r["model"], r["pk"]): r for r in payload["records"]}
            actual_by_key = {(r["model"], r["pk"]): r for r in actual_records}
            missing = sorted(set(expected_by_key) - set(actual_by_key))[:10]
            extra = sorted(set(actual_by_key) - set(expected_by_key))[:10]
            changed = [
                key for key in sorted(set(expected_by_key) & set(actual_by_key))
                if expected_by_key[key] != actual_by_key[key]
            ][:10]
            raise CommandError(
                "JSON/database snapshot digest mismatch: "
                f"missing={missing}, extra={extra}, changed={changed}"
            )

        if User.objects.exists():
            raise CommandError("Snapshot database contains user records")
        for label in sorted(FORBIDDEN_RUNTIME_LABELS):
            try:
                model = apps.get_model(label)
            except LookupError:
                # The label is forward-compatible with apps that are not
                # installed in this deployment.
                model = None
            if model is not None and model.objects.exists():
                raise CommandError(f"Snapshot database contains forbidden runtime rows: {label}")
        secret_key = re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password|credential|private[_-]?key)")
        for setting in SiteSetting.objects.all():
            stack = [setting.value]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    for key, child in value.items():
                        if secret_key.search(str(key)) and child not in (None, "", [], {}):
                            raise CommandError(f"Secret-like SiteSetting value is present: {setting.key}")
                        stack.append(child)
                elif isinstance(value, list):
                    stack.extend(value)
        expected_destinations = payload["counts"].get("tourist.destination", 0)
        if Destination.objects.count() != expected_destinations:
            raise CommandError("Snapshot database destination count does not match JSON")
        invalid = Destination.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        ).exclude(latitude__gte=26, latitude__lte=31, longitude__gte=80, longitude__lte=89)
        if invalid.exists():
            raise CommandError("Snapshot database contains out-of-Nepal destination coordinates")

        if connection.vendor == "sqlite":
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
            if result != "ok":
                raise CommandError(f"SQLite integrity_check failed: {result}")

        call_command("check", verbosity=0)
        self.stdout.write(self.style.SUCCESS(
            f"Verified snapshot OK: {len(actual['records'])} records, "
            f"{expected_destinations} destinations, sha256={actual['records_sha256']}"
        ))
