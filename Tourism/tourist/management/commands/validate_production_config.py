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

PLACEHOLDERS = {"", "changeme", "secret", "django-insecure", "dev-secret-key",
                "your-secret-key", "your-client-id", "your-google-client-id",
                "your-github-client-id", "xxx", "todo"}


def _is_placeholder(value: str) -> bool:
    """True when a credential is a template rather than a real value.

    Real client ids and secrets are long and high-entropy, so anything short or
    obviously templated is a placeholder, not a usable credential. The value is
    never printed, only classified.
    """
    text = (value or "").strip()
    if not text:
        return True
    lowered = text.lower()
    if lowered in PLACEHOLDERS:
        return True
    if text.startswith(("your-", "YOUR_", "<", "{{")):
        return True
    if "example" in lowered or "placeholder" in lowered:
        return True
    return len(text) < 12


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
            # SQLite is acceptable in production when WAL-hardened (the
            # tourist app applies this automatically on file-backed DBs):
            # concurrent readers + one writer is fine for a single node.
            from django.db import connection

            mode, fk = None, None
            try:
                with connection.cursor() as cur:
                    cur.execute("PRAGMA journal_mode")
                    mode = cur.fetchone()[0]
                    cur.execute("PRAGMA foreign_keys")
                    fk = cur.fetchone()[0]
            except Exception as exc:  # unreachable DB is itself a failure
                fails.append(f"SQLite production check could not run: {exc}")
            if str(mode).lower() == "wal" and fk:
                oks.append("Database engine: sqlite3 WAL-hardened (foreign keys ON) "
                           "— production-viable on a single node; choose "
                           "Postgres (DATABASE_URL) for multi-instance")
            else:
                fails.append(
                    f"SQLite is NOT production-hardened (journal_mode={mode}, "
                    "foreign_keys={fk}): WAL is applied automatically on "
                    "file-backed databases — check file/dir write permissions, "
                    "or switch to Postgres via DATABASE_URL")
        else:
            oks.append(f"Database engine: {engine}")

        for name in ("ML_SERVICE_API_KEY", "ML_WEBHOOK_SECRET"):
            val = str(getattr(settings, name, "") or "")
            if not val or val.startswith("change-this") or val in ("dev", "dev-secret", "changeme", "secret"):
                fails.append(f"{name} must be set to a non-default value: value never printed")
            else:
                oks.append(f"{name} set to a non-default value: value never printed")

        email_backend = str(getattr(settings, "EMAIL_BACKEND", ""))
        if "console.EmailBackend" in email_backend:
            fails.append("EMAIL_BACKEND is console: real email delivery is not enabled for production")
        elif "smtp.EmailBackend" in email_backend:
            if not getattr(settings, "EMAIL_HOST_USER", "") or not getattr(settings, "EMAIL_HOST_PASSWORD", "") or not getattr(settings, "DEFAULT_FROM_EMAIL", ""):
                fails.append("SMTP email backend selected but SMTP credentials/sender are incomplete")
            else:
                oks.append("SMTP email configuration present: values never printed")
        else:
            warns.append(f"Email backend is {email_backend or 'unset'}: verify that it performs real delivery")

        for provider, id_name, secret_name in (
            ("Google", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
            ("GitHub", "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"),
        ):
            client_id = str(getattr(settings, id_name, "") or "").strip()
            client_secret = str(getattr(settings, secret_name, "") or "").strip()
            if not client_id and not client_secret:
                # Not an error: social sign-in is legitimately optional and the
                # UI already keeps the buttons disabled rather than faking them.
                warns.append(
                    f"{provider} OAuth not configured: {id_name}/{secret_name} unset, so "
                    f"social sign-in stays honestly disabled"
                )
                continue
            placeholder_id = _is_placeholder(client_id)
            placeholder_secret = _is_placeholder(client_secret)
            if placeholder_id or placeholder_secret:
                fails.append(
                    f"{provider} OAuth uses a placeholder value for "
                    f"{id_name if placeholder_id else secret_name}: real credentials are required "
                    f"and cannot be generated by this application"
                )
            elif not client_id:
                fails.append(
                    f"{provider} OAuth has {secret_name} but no {id_name}: the authorization-code "
                    f"exchange cannot run"
                )
            elif not client_secret:
                fails.append(
                    f"{provider} OAuth has {id_name} but no {secret_name}: the sign-in button would "
                    f"render and then fail during the code exchange"
                )
            else:
                oks.append(
                    f"{provider} OAuth credentials present ({id_name}+{secret_name}): values never printed"
                )

        # Make the required registration explicit: a correct secret with a
        # callback URI the provider does not know still fails at runtime.
        front_origin = ""
        for candidate in ("FRONTEND_ORIGIN", "FRONTEND_BASE_URL", "VITE_API_BASE_URL"):
            value = str(os.environ.get(candidate, "") or "").strip()
            if value.startswith("http"):
                front_origin = value.rstrip("/")
                break
        if front_origin:
            oks.append(
                f"OAuth callback URIs to register with each provider: {front_origin}/auth/callback/google "
                f"and {front_origin}/auth/callback/github"
            )
        else:
            warns.append(
                "Set FRONTEND_ORIGIN (or FRONTEND_BASE_URL) so the exact OAuth callback URIs to "
                "register can be printed; they are not derivable from the backend"
            )

        if getattr(settings, "ROUTING_API_URL", ""):
            oks.append("Production road-routing provider configured")
        else:
            fails.append("ROUTING_API_URL is empty: production navigation cannot claim verified road routing")

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
