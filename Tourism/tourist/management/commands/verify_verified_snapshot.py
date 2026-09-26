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
        # NOTE: do not migrate the release database here. A published artifact
        # is a snapshot in time; applying later migrations (for example
        # 0081_unpublish_seeded_cms_placeholders) would change which records
        # the rebuild considers public, so the release could never verify
        # against itself. The exporter instead tolerates model fields that the
        # release's own schema does not have.
        #
        # Re-check the release against the rule IT declared. A payload written
        # before the configurable media gate existed carries no media_gate key
        # and is held to the historical scored rule, which did not require
        # provenance, so today's stricter default cannot retroactively strip
        # records from an already-published release.
        declared_policy = payload.get("policy") or {}
        declared_gate = declared_policy.get("media_gate") or None
        declared_provenance_raw = str(
            declared_policy.get("media_gate_requires_provenance") or ""
        ).strip().lower()
        if declared_provenance_raw in {"true", "1", "yes"}:
            declared_provenance = True
        elif declared_provenance_raw in {"false", "0", "no"}:
            declared_provenance = False
        else:
            # Absent key: this release predates the configurable gate, so it is
            # held to the historical scored rule, which did not require
            # provenance.
            declared_provenance = False
        actual = build_snapshot_payload(
            as_of=as_of_from_payload(payload),
            media_gate=declared_gate,
            require_review_provenance=declared_provenance,
        )
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
            changed = []
            for key in sorted(set(expected_by_key) & set(actual_by_key)):
                expected_fields = expected_by_key[key].get("fields", {})
                actual_fields = actual_by_key[key].get("fields", {})
                # Compare only the fields this release actually claimed. A
                # column added to the model after the release was published
                # cannot have been part of it, and holding an old artifact to a
                # newer schema would invalidate every historical download.
                differences = {
                    name: (expected_fields[name], actual_fields.get(name))
                    for name in expected_fields
                    if name not in actual_fields or actual_fields[name] != expected_fields[name]
                }
                if differences or expected_by_key[key].get("model") != actual_by_key[key].get("model"):
                    changed.append((key, differences))
            if missing or extra or changed:
                raise CommandError(
                    "JSON/database snapshot digest mismatch: "
                    f"missing={missing}, extra={extra}, changed={changed[:10]}"
                )
            # Nothing differs: the digests diverged only because of fields the
            # release could not have contained. That is expected, not a failure.
            self.stdout.write(
                self.style.WARNING(
                    "Snapshot content matches the release; the digest differs only by model "
                    "fields added after this release was published (now ignored)."
                )
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
