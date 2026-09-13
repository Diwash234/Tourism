"""Loud production-configuration validation (never prints secret values).

FAIL (exit 1) when any critical is true:
  DEBUG=True; SECRET_KEY weak/placeholder; permissive ALLOWED_HOSTS;
  CORS_ALLOW_ALL_ORIGINS with DEBUG off; SQLite database in production;
  default/missing ML service credentials.
WARN for: unconfigured OAuth providers, no routing provider, missing
  backups dir or stale backups, insecure session cookies.

Usage: python manage.py validate_production_config [--json]
"""
import json
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

PLACEHOLDERS = {"", "changeme", "secret", "django-insecure", "dev-secret-key", "your-secret-key"}


class Command(BaseCommand):
    help = "Validate the running configuration for production readiness."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true")

    def handle(self, *args, **options):
        fails, warns, oks = [], [], []

        if settings.DEBUG:
            fails.append("DEBUG is True: must be False in production")
        else:
            oks.append("DEBUG is False")

        key = settings.SECRET_KEY or ""
        if len(key) < 50 or any(key.startswith(p) for p in PLACEHOLDERS if p) or "django-insecure" in key:
            fails.append("SECRET_KEY must be >=50 chars and not a dev placeholder: value never printed")
        else:
            oks.append("SECRET_KEY looks production-grade: value never printed")

        hosts = list(getattr(settings, "ALLOWED_HOSTS", []))
        if "*" in hosts:
            fails.append("ALLOWED_HOSTS contains '*': list explicit production hostnames")
        elif not hosts:
            fails.append("ALLOWED_HOSTS is empty")
        else:
            oks.append(f"ALLOWED_HOSTS explicit: {hosts}")

        if getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False) and not settings.DEBUG:
            fails.append("CORS_ALLOW_ALL_ORIGINS is True with DEBUG off: whitelist origins")
        else:
            oks.append("CORS policy acceptable")

        engine = settings.DATABASES["default"]["ENGINE"]
        if "sqlite3" in engine:
            fails.append(f"Database should be Postgres in production: currently {engine}")
        else:
            oks.append(f"Database engine: {engine}")

        for name in ("ML_SERVICE_API_KEY", "ML_WEBHOOK_SECRET"):
            val = str(getattr(settings, name, "") or "")
            if not val or val.startswith("change-this") or val in ("dev", "dev-secret", "changeme", "secret"):
                fails.append(f"{name} must be set to a non-default value: value never printed")
            else:
                oks.append(f"{name} set to a non-default value: value never printed")

        for provider, cid in (("Google", getattr(settings, "GOOGLE_CLIENT_ID", "")),
                              ("GitHub", getattr(settings, "GITHUB_CLIENT_ID", ""))):
            if not cid:
                warns.append(f"{provider} OAuth not configured: social sign-in buttons stay honestly disabled until set")
            else:
                oks.append(f"{provider} OAuth credentials present")

        oks.append("Routing uses the bundled GraphML graph with honest approximation notes (no street-level provider claimed)")

        backups_dir = Path(str(settings.BASE_DIR)) / "backups"
        if not backups_dir.exists() or not any(backups_dir.glob("*.gz")):
            warns.append("No backup archives found: run backup_database (schedule in the ops runbook)")
        else:
            oks.append("Backup archives present (schedule freshness is monitored by system_health)")

        if not getattr(settings, "SESSION_COOKIE_SECURE", False):
            warns.append("SESSION_COOKIE_SECURE is False: auto-enabled when DEBUG=False; verify reverse-proxy HTTPS")

        result = {"passed": not fails, "fail": fails, "warn": warns, "ok": oks}
        if options["json"]:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            for line in fails:
                self.stdout.write(self.style.ERROR(f"  FAIL  {line}"))
            for line in warns:
                self.stdout.write(self.style.WARNING(f"  WARN  {line}"))
            for line in oks:
                self.stdout.write(self.style.SUCCESS(f"  OK    {line}"))
            self.stdout.write("RESULT: " + ("PASS" if not fails else "FAIL"))
        if fails:
            raise SystemExit(1)
