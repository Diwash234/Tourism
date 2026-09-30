"""
Project-wide production readiness gate.

This command is deliberately non-destructive: it reports measurable gaps and
fails only when --strict is requested. It is safe to run against development,
CI, staging, or Render PostgreSQL and never mutates tourism records.
"""
import json
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection
from django.db.models import Q


class Command(BaseCommand):
    help = "Run the Nepal Yatra production-readiness audit."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Exit non-zero when a required gate fails.")
        parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    def handle(self, *args, **options):
        report = {"status": "pass", "checks": {}, "warnings": [], "failures": []}

        def check(name, ok, detail, required=True):
            report["checks"][name] = {"ok": bool(ok), "detail": detail, "required": required}
            if not ok:
                (report["failures"] if required else report["warnings"]).append(
                    {"check": name, "detail": detail}
                )

        # Database connectivity/integrity.
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            check("database", True, connection.vendor)
        except Exception as exc:
            check("database", False, f"{type(exc).__name__}: {exc}")

        # Migration graph must be clean. This is a code-level check and does
        # not apply or alter migrations.
        try:
            from io import StringIO
            output = StringIO()
            call_command("migrate", check=True, verbosity=0, stdout=output)
            check("migrations", True, "migration graph is consistent")
        except Exception as exc:
            check("migrations", False, f"{type(exc).__name__}: {exc}")

        Destination = apps.get_model("tourist", "Destination")
        Hotel = apps.get_model("tourist", "Hotel")
        DestinationImage = apps.get_model("tourist", "DestinationImage")

        approved = Destination.objects.filter(
            is_active=True, status="approved"
        )
        destination_count = approved.count()
        check("approved_destinations", destination_count > 0, f"{destination_count} approved destinations")

        missing_coords = approved.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        ).count()
        check("destination_coordinates", missing_coords == 0,
              f"{missing_coords} approved destinations missing coordinates", required=False)

        missing_admin = approved.filter(
            Q(district__isnull=True) | Q(district="") |
            Q(province__isnull=True) | Q(province="")
        ).count()
        check("destination_admin_areas", missing_admin == 0,
              f"{missing_admin} approved destinations missing province/district", required=False)

        image_count = DestinationImage.objects.filter(destination__in=approved).count()
        check("destination_media", image_count > 0, f"{image_count} destination media records")

        hotel_count = Hotel.objects.filter(is_active=True).count()
        check("hotel_catalogue", True, f"{hotel_count} active hotel records", required=False)

        # Frontend build is required in the Render container, but not in local
        # development where Vite serves the SPA separately.
        frontend_index = settings.FRONTEND_DIST_DIR / "index.html"
        check(
            "frontend_build",
            frontend_index.is_file() or settings.DEBUG,
            str(frontend_index) if frontend_index.is_file() else "not installed (allowed while DEBUG=True)",
            required=not settings.DEBUG,
        )

        check("secret_key", bool(settings.SECRET_KEY) and (
            settings.DEBUG or "django-insecure" not in settings.SECRET_KEY
        ), "configured" if settings.SECRET_KEY else "missing")

        check("debug", not settings.DEBUG, "DEBUG=False" if not settings.DEBUG else "DEBUG=True", required=False)

        report["status"] = "fail" if report["failures"] else ("warn" if report["warnings"] else "pass")

        payload = json.dumps(report, indent=2, default=str)
        if options["json"]:
            self.stdout.write(payload)
        else:
            self.stdout.write(self.style.SUCCESS(f"Readiness: {report['status'].upper()}"))
            for name, result in report["checks"].items():
                marker = "PASS" if result["ok"] else ("WARN" if not result["required"] else "FAIL")
                self.stdout.write(f"[{marker}] {name}: {result['detail']}")
            if report["failures"]:
                self.stdout.write(self.style.ERROR(f"{len(report['failures'])} required gate(s) failed."))
            if report["warnings"]:
                self.stdout.write(self.style.WARNING(f"{len(report['warnings'])} advisory gate(s) need attention."))

        if options["strict"] and report["failures"]:
            raise SystemExit(1)
