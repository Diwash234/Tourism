import shutil
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Export application data from current SQLite/PostgreSQL database to a portable JSON fixture."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="data.json", help="Output fixture path (default: data.json).")
        parser.add_argument("--include-audit", action="store_true", help="Include audit logs and error events.")

    def handle(self, *args, **options):
        output = Path(options["output"]).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        excludes = [
            "contenttypes",
            "auth.permission",
            "admin.logentry",
            "sessions",
            "token_blacklist",
        ]
        if not options.get("include_audit"):
            excludes.extend(["audit.auditlog", "audit.errorevent"])

        self.stdout.write(f"Exporting database data to {output} ...")
        with output.open("w", encoding="utf-8") as stream:
            call_command(
                "dumpdata",
                *[item for exclude in excludes for item in ("--exclude", exclude)],
                "--natural-foreign",
                "--natural-primary",
                "--indent",
                "2",
                stdout=stream,
            )

        file_size_mb = output.stat().st_size / (1024 * 1024)
        self.stdout.write(
            self.style.SUCCESS(f"Created portable fixture: {output} ({file_size_mb:.2f} MB)")
        )

        # Mirror file to the other standard name (data.json <-> load.json) so
        # Render and entrypoint scripts find it whichever convention is used.
        if output.name == "data.json":
            alt = output.with_name("load.json")
            try:
                shutil.copy2(output, alt)
                self.stdout.write(self.style.SUCCESS(f"Created companion copy: {alt}"))
            except Exception:
                pass
        elif output.name == "load.json":
            alt = output.with_name("data.json")
            try:
                shutil.copy2(output, alt)
                self.stdout.write(self.style.SUCCESS(f"Created companion copy: {alt}"))
            except Exception:
                pass

        # Summary of exported counts
        self.stdout.write("\nExported core records:")
        for model_name in [
            "tourist.Destination",
            "tourist.DestinationImage",
            "tourist.Hotel",
            "tourist.Hospital",
            "tourist.PoliceStation",
            "tourist.User",
            "tourist.ManagedPage",
        ]:
            try:
                model = apps.get_model(model_name)
                self.stdout.write(f"  {model_name}: {model.objects.count()}")
            except Exception:
                pass
