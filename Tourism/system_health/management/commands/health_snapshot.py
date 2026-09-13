"""
Run all health checks, print a human readable report, and write a
HealthSample row. Useful for cron jobs, Docker HEALTHCHECK, and manual
diagnostics:

    python manage.py health_snapshot
    python manage.py health_snapshot --json
"""
import json
from django.core.management.base import BaseCommand
from system_health.checks import run_all_checks, write_snapshot


class Command(BaseCommand):
    help = "Run system health diagnostics and record a snapshot"

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true",
                            help="Output full report as JSON")
        parser.add_argument("--no-save", action="store_true",
                            help="Only print, don't save to DB")

    def handle(self, *args, **opts):
        r = run_all_checks()
        if opts["json"]:
            self.stdout.write(json.dumps(r, indent=2, default=str))
        else:
            status_icon = "✓" if r["ok"] else "✗"
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"\nSystem health: {status_icon} {'OK' if r['ok'] else 'DEGRADED'} @ {r['checked_at']}\n"
            ))
            for name, data in r["checks"].items():
                ok = data.get("ok")
                icon = "✓" if ok else ("?" if ok is None else "✗")
                line = f"  {icon} {name:<18}"
                details = []
                for k, v in data.items():
                    if k == "ok": continue
                    if k == "error":
                        details.append(self.style.ERROR(f"err={v}"))
                    else:
                        details.append(f"{k}={v}")
                self.stdout.write(line + "  " + " | ".join(map(str, details)))
        if not opts["no_save"]:
            s = write_snapshot()
            self.stdout.write(self.style.SUCCESS(
                f"\nSaved HealthSample id={s.pk}  overall={s.overall()}\n"
            ))
