"""Load a canonical verified tourism JSON snapshot into an empty runtime DB."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, transaction

from tourist.models import Destination, User
from tourist.verified_snapshot import MODEL_ORDER, read_payload, validate_payload


class Command(BaseCommand):
    help = "Load the canonical tourism snapshot without importing users or runtime state."

    def add_arguments(self, parser):
        parser.add_argument("input", help="Path to verified_tourism_data.json.")
        parser.add_argument(
            "--allow-empty-tourism-runtime",
            action="store_true",
            help="Internal build option: permit migration-seeded CMS rows but no destinations/users.",
        )

    def handle(self, *args, **options):
        path = Path(options["input"])
        if not path.exists():
            raise CommandError(f"Snapshot JSON not found: {path}")
        payload = read_payload(path)
        validate_payload(payload)

        if User.objects.exists():
            raise CommandError(
                "Refusing to load the public snapshot into a database containing users. "
                "Use a fresh SQLite database; runtime accounts are never merged."
            )
        if Destination.objects.exists():
            raise CommandError(
                "Refusing to merge the public snapshot into a database that already has destinations. "
                "Build or restore into a fresh database instead."
            )

        fixture = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            prefix="nepal-yatra-verified-",
            encoding="utf-8",
            delete=False,
        )
        try:
            json.dump(
                payload["records"],
                fixture,
                ensure_ascii=False,
                cls=DjangoJSONEncoder,
            )
            fixture.write("\n")
            fixture.close()
            with transaction.atomic():
                # Fresh migrations seed default languages/CMS rows with
                # different primary keys than the source snapshot.  Remove
                # only the allowlisted seed/reference models before loading so
                # unique keys/routes cannot collide.  Operational models and
                # migration history remain untouched.
                for model in reversed(MODEL_ORDER):
                    model.objects.all().delete()
                call_command("loaddata", fixture.name, verbosity=0)
                connection.check_constraints()
        finally:
            try:
                fixture.close()
            except Exception:
                pass
            Path(fixture.name).unlink(missing_ok=True)

        expected_destinations = payload["counts"].get("tourist.destination", 0)
        actual_destinations = Destination.objects.count()
        if actual_destinations != expected_destinations:
            raise CommandError(
                f"Snapshot destination count mismatch: expected {expected_destinations}, "
                f"loaded {actual_destinations}."
            )
        if User.objects.exists():
            raise CommandError("Snapshot import unexpectedly created user records.")

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(payload['records'])} verified data records "
            f"({actual_destinations} destinations); no user/runtime records imported."
        ))
