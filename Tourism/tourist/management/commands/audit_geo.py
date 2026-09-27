"""Audit stored coordinates and report how far each can be trusted.

The validators only protect writes that go through them. This command answers
the question nobody can otherwise answer: how many positions already in the
database are unusable, and why?

    python manage.py audit_geo
    python manage.py audit_geo --json
    python manage.py audit_geo --destination
    python manage.py audit_geo --quarantine-null-island

``--quarantine-null-island`` clears only the (0, 0) values, which are
unambiguously broken rather than merely suspicious, and records why. It never
guesses a replacement coordinate.
"""
from __future__ import annotations

import json
from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from tourist.geo_validation import (
    QUALITY_UNUSABLE,
    validate_fix,
)
from tourist.models import Destination, User


class Command(BaseCommand):
    help = "Report the validation state of stored user and destination coordinates."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true")
        parser.add_argument(
            "--destination",
            action="store_true",
            help="Also audit destination coordinates, not just users.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="How many example rows to print per reason.",
        )
        parser.add_argument(
            "--quarantine-null-island",
            action="store_true",
            help="Clear coordinates that are exactly (0, 0); no replacement is guessed.",
        )

    def handle(self, *args, **options):
        report = {
            "generated_at": timezone.now().isoformat(),
            "users": self._audit_users(options),
        }
        if options["destination"]:
            report["destinations"] = self._audit_destinations(options)

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, default=str))
            return
        self._render(report, options)

    # -- audits ------------------------------------------------------------

    def _audit_users(self, options) -> dict:
        states: Counter = Counter()
        reasons: Counter = Counter()
        examples: dict[str, list] = {}
        null_island = []

        queryset = User.objects.exclude(latitude=None).exclude(longitude=None)
        total = queryset.count()
        for user in queryset.iterator(chunk_size=500):
            fix = validate_fix(user.latitude, user.longitude, source=user.location_source or "gps")
            states[fix.quality] += 1
            for reason in fix.reasons:
                reasons[reason] += 1
                bucket = examples.setdefault(reason, [])
                if len(bucket) < options["limit"]:
                    bucket.append(user.email)
            if "null_island" in fix.reasons:
                null_island.append(user)

        quarantined = 0
        if options["quarantine_null_island"] and null_island:
            for user in null_island:
                user.latitude = None
                user.longitude = None
                user.location_source = ""
                user.gps_validated_at = timezone.now()
                user.gps_validation_state = "unusable"
                user.gps_validation_reasons = ["null_island", "quarantined_by_audit"]
                user.save(
                    update_fields=[
                        "latitude", "longitude", "location_source",
                        "gps_validated_at", "gps_validation_state", "gps_validation_reasons",
                    ]
                )
                quarantined += 1

        return {
            "rows_with_coordinates": total,
            "quality": dict(states),
            "reasons": dict(reasons),
            "examples": examples,
            "null_island_quarantined": quarantined,
        }

    def _audit_destinations(self, options) -> dict:
        states: Counter = Counter()
        reasons: Counter = Counter()
        queryset = Destination.objects.exclude(latitude=None).exclude(longitude=None)
        total = queryset.count()
        for destination in queryset.iterator(chunk_size=500):
            fix = validate_fix(destination.latitude, destination.longitude, source="destination")
            states[fix.quality] += 1
            for reason in fix.reasons:
                reasons[reason] += 1
        return {
            "rows_with_coordinates": total,
            "quality": dict(states),
            "reasons": dict(reasons),
        }

    # -- output ------------------------------------------------------------

    def _render(self, report, options) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Stored coordinate audit"))
        self.stdout.write(f"  generated at: {report['generated_at']}")

        for label in ("users", "destinations"):
            section = report.get(label)
            if not section:
                continue
            self.stdout.write("")
            self.stdout.write(f"  {label}: {section['rows_with_coordinates']} rows with coordinates")
            for quality, count in sorted(section["quality"].items()):
                self.stdout.write(f"    {quality:<14} {count}")
            if section["reasons"]:
                self.stdout.write("    reasons:")
                for reason, count in sorted(section["reasons"].items(), key=lambda kv: -kv[1]):
                    self.stdout.write(f"      {reason:<22} {count}")
                    examples = section.get("examples", {}).get(reason)
                    if examples:
                        self.stdout.write(f"        e.g. {examples[:5]}")
            if section.get("null_island_quarantined"):
                self.stdout.write(
                    self.style.WARNING(
                        f"    quarantined {section['null_island_quarantined']} null-island positions "
                        "(coordinates cleared, nothing guessed)"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            "  'approximate' is normal: a position with no reported accuracy or "
            "timestamp is still usable, it just cannot be called precise."
        )
        self.stdout.write(
            "  'unusable' rows never reach a map pin or a distance calculation; "
            "the API returns a reason instead."
        )
