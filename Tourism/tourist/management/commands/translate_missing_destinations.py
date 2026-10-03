"""Auto-translate destinations missing a translation in ne/hi.

Best-effort: skips when the MT engine is rate-limited or down.
Run periodically (cron/Render cron) so newly added content gets
conversion options without manual work:

    python manage.py translate_missing_destinations
    python manage.py translate_missing_destinations --lang ne --limit 50
"""
import time

from django.core.management.base import BaseCommand

from tourist.models import Destination, DestinationTranslation, Language
from tourist.utils import translate_text


class Command(BaseCommand):
    help = "Machine-translate destinations missing ne/hi translations."

    def add_arguments(self, parser):
        parser.add_argument("--lang", default="ne,hi")
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--force", action="store_true",
                            help="re-translate even auto-generated rows")

    def handle(self, *args, **options):
        langs = [c.strip() for c in options["lang"].split(",") if c.strip()]
        total = 0
        for code in langs:
            try:
                language = Language.objects.get(code=code)
            except Language.DoesNotExist:
                self.stderr.write(f"Language '{code}' not found, skipping")
                continue
            qs = Destination.objects.filter(is_active=True)
            if not options["force"]:
                done_ids = DestinationTranslation.objects.filter(
                    language=language, is_auto_generated=False
                ).values_list("destination_id", flat=True)
                # Also skip fresh auto rows; only fill truly missing ones.
                auto_ids = DestinationTranslation.objects.filter(
                    language=language, is_auto_generated=True
                ).values_list("destination_id", flat=True)
                qs = qs.exclude(pk__in=list(done_ids) + list(auto_ids))
            qs = qs.order_by("id")[:options["limit"]]
            for dest in qs.iterator():
                try:
                    name = translate_text(dest.name or "", code) or dest.name
                    desc = translate_text(dest.description or "", code) or dest.description
                    short = translate_text(dest.short_description or "", code) or dest.short_description
                except Exception as exc:  # noqa: BLE001
                    self.stderr.write(f"  MT failed for {dest.name}: {exc}")
                    time.sleep(5)
                    continue
                DestinationTranslation.objects.update_or_create(
                    destination=dest, language=language,
                    defaults={"name": name, "description": desc,
                              "short_description": short, "is_auto_generated": True},
                )
                total += 1
                time.sleep(1)
            self.stdout.write(f"[{code}] translated {total} destinations")
        self.stdout.write(self.style.SUCCESS(f"Done. {total} new auto-translations."))
