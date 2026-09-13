"""Data freshness: verified data must not stay "verified" forever.

Scans every model that carries the (is_verified, verified_at) contract —
Hospital, PoliceStation, BudgetEstimation, EmergencyNumber, and any future
model with the same fields — and reports how many verified records have
gone stale (verified_at older than the configured interval).

With --flag, stale records have is_verified set back to False so the UI's
"verified" badge honestly disappears until a human re-verifies them.
Records that were NEVER verified (verified_at NULL) are reported but never
touched — we don't invent verification history.

Interval precedence: --interval-days > settings.VERIFICATION_INTERVAL_DAYS
> 180 (six months, matching the review requirement example).

Usage:
    python manage.py flag_stale_verifications                 # report only
    python manage.py flag_stale_verifications --flag          # expire stale rows
    python manage.py flag_stale_verifications --interval-days 90 --flag
"""
import json
import os
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


def verification_models():
    """Every concrete model implementing the (is_verified, verified_at) contract."""
    out = []
    for model in apps.get_models():
        fields = {f.name for f in model._meta.get_fields()}
        if {"is_verified", "verified_at"} <= fields:
            out.append(model)
    return out


class Command(BaseCommand):
    help = "Report (and optionally expire) verified records older than the verification interval."

    def add_arguments(self, parser):
        parser.add_argument("--interval-days", type=int, default=None,
                            help="Override settings.VERIFICATION_INTERVAL_DAYS (default 180)")
        parser.add_argument("--flag", action="store_true",
                            help="Set is_verified=False on stale records (default: report only)")
        parser.add_argument("--report", default=None, help="Write a JSON report to this path")

    def handle(self, *args, **options):
        days = options["interval_days"] or getattr(settings, "VERIFICATION_INTERVAL_DAYS", 180)
        cutoff = timezone.now() - timedelta(days=days)
        report = {"interval_days": days, "cutoff": cutoff.isoformat(), "flagged": options["flag"], "models": {}}

        total_stale = total_flagged = 0
        for model in verification_models():
            label = model._meta.label
            verified_qs = model.objects.filter(is_verified=True)
            verified = verified_qs.count()
            stale_qs = verified_qs.filter(verified_at__isnull=False, verified_at__lt=cutoff)
            stale = stale_qs.count()
            never = model.objects.filter(is_verified=True, verified_at__isnull=True).count()
            unverified = model.objects.filter(is_verified=False).count()
            flagged = 0
            if options["flag"] and stale:
                flagged = stale_qs.update(is_verified=False)
            report["models"][label] = {
                "verified": verified, "stale": stale, "flagged": flagged,
                "verified_without_timestamp": never, "unverified": unverified,
            }
            total_stale += stale
            total_flagged += flagged
            self.stdout.write(
                f"{label}: verified={verified} stale={stale}"
                + (f" flagged={flagged}" if options["flag"] else "")
                + f" verified_without_timestamp={never} unverified={unverified}"
            )

        report["totals"] = {"stale": total_stale, "flagged": total_flagged}
        self.stdout.write(f"TOTAL stale={total_stale}" + (f" flagged={total_flagged}" if options["flag"] else ""))

        if options["report"]:
            os.makedirs(os.path.dirname(options["report"]) or ".", exist_ok=True)
            with open(options["report"], "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.stdout.write(f"Report: {options['report']}")
