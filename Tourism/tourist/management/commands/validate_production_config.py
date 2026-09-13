"""Production configuration validator (§15).

Fails loudly (exit code 1) when production-critical configuration is wrong
or missing; warns for recommended-but-optional items. NEVER prints secret
values — only whether each credential is set.

    python manage.py validate_production_config
    python manage.py validate_production_config --json
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Validate production-critical configuration. Exit 1 on any FAIL."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Machine-readable output")

    def handle(self, *args, **options):
        fails, warns, oks = [], [], []

        def check(ok, label, detail=""):
            (oks if ok else fails).append(f"{label}" + (f": {detail}" if detail else ""))

        def warn(label, detail=""):
            warns.append(f"{label}" + (f": {detail}" if detail else ""))

        # --- critical ---
        check(not settings.DEBUG, "DEBUG must be False in production", f"currently {settings.DEBUG}")
        key = settings.SECRET_KEY or ""
        dev_defaults = {"django-insecure", "changeme", "replace-with"}
        check(len(key) >= 50 and not any(key.startswith(p) for p in dev_defaults),
              "SECRET_KEY must be >=50 chars and not a dev placeholder", "value never printed")
        allowed = list(getattr(settings, "ALLOWED_HOSTS", []) or [])
        check(bool(allowed) and allowed != ["*"], "ALLOWED_HOSTS must list explicit hosts", f"currently {allowed or 'empty'}")
        check(not getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False),
              "CORS_ALLOW_ALL_ORIGINS must be False in production")
        engine = settings.DATABASES["default"]["ENGINE"]
        check("sqlite" not in engine, "Database should be Postgres in production", f"currently {engine}")
        check(bool(settings.ML_SERVICE_API_KEY) and settings.ML_SERVICE_API_KEY != "change-this-ml-api-key",
              "ML_SERVICE_API_KEY must be set to a non-default value", "value never printed")
        check(bool(settings.ML_WEBHOOK_SECRET) and settings.ML_WEBHOOK_SECRET != "change-this-shared-secret",
              "ML_WEBHOOK_SECRET must be set to a non-default value", "value never printed")

        # --- recommended (warnings, do not fail the deploy) ---
        for name, label in (("GOOGLE_CLIENT_ID", "Google OAuth"), ("GITHUB_CLIENT_ID", "GitHub OAuth")):
            cid = getattr(settings, name, "")
            sec = getattr(settings, name.replace("CLIENT_ID", "CLIENT_SECRET"), "")
            if cid and sec:
                oks.append(f"{label} credentials configured (values never printed)")
            else:
                warn(f"{label} not configured", "social sign-in buttons stay honestly disabled until set")
        from tourist.models import SiteSetting
        provider = SiteSetting.objects.filter(key="routing_provider").first()
        if provider and str(getattr(provider, "value", "") or "").strip():
            oks.append("Routing provider configured")
        else:
            warn("Routing provider not configured", "graph fallback stays active; street-level routing off")
        import os
        backup_dir = os.path.join(str(settings.BASE_DIR.parent), "backups")
        if os.path.isdir(backup_dir) and any(n.endswith(".sqlite3.gz") for n in os.listdir(backup_dir)):
            oks.append("Backup archives present (schedule freshness is monitored by system_health)")
        else:
            warn("No backups found", "run manage.py backup_database and schedule it daily")
        if getattr(settings, "SESSION_COOKIE_SECURE", False):
            oks.append("Secure cookies enabled")
        else:
            warn("SESSION_COOKIE_SECURE is False", "auto-enabled when DEBUG=False; verify reverse-proxy HTTPS")

        result = {"fail": fails, "warn": warns, "ok": oks, "passed": not fails}
        if options["json"]:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            for line in oks:
                self.stdout.write(self.style.SUCCESS(f"  OK   {line}"))
            for line in warns:
                self.stdout.write(self.style.WARNING(f"  WARN {line}"))
            for line in fails:
                self.stdout.write(self.style.ERROR(f"  FAIL {line}"))
            self.stdout.write(
                self.style.SUCCESS("PRODUCTION CONFIG VALID") if not fails
                else self.style.ERROR(f"PRODUCTION CONFIG INVALID — {len(fails)} critical problem(s)")
            )
        if fails:
            raise SystemExit(1)
