from pathlib import Path

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Export application data from the current database to a portable JSON fixture."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="data.json", help="Output fixture path.")

    def handle(self, *args, **options):
        output = Path(options["output"]).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        excludes = ["contenttypes", "auth.permission", "admin.logentry", "sessions", "token_blacklist"]
        self.stdout.write(f"Exporting database data to {output} ...")
        with output.open("w", encoding="utf-8") as stream:
            call_command(
                "dumpdata",
                *[item for exclude in excludes for item in ("--exclude", exclude)],
                "--natural-foreign", "--natural-primary", "--indent", "2",
                stdout=stream,
            )
        self.stdout.write(self.style.SUCCESS(f"Created portable fixture: {output}"))
