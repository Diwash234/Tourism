"""Seed UITranslation rows from the frontend's bundled i18n dictionary.

Parses frontend/Tourism/src/i18n/index.js, extracts the per-language
`const XX = {...}` blocks, and upserts every key/value into
UITranslation. Existing admin edits are overwritten only when
--force is passed; by default only missing rows are created.

Usage:
    python manage.py seed_ui_translations
    python manage.py seed_ui_translations --force
    python manage.py seed_ui_translations --lang ne
"""
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from tourist.models import UITranslation


class Command(BaseCommand):
    help = "Seed UITranslation rows from the frontend bundled i18n dictionary."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="overwrite existing rows with bundled values")
        parser.add_argument("--lang", default="",
                            help="only seed this language code (e.g. ne)")

    def handle(self, *args, **options):
        i18n_path = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "frontend" / "Tourism" / "src" / "i18n" / "index.js"
        )
        if not i18n_path.exists():
            self.stderr.write(f"i18n bundle not found at {i18n_path}")
            return

        text = i18n_path.read_text(encoding="utf-8")
        created = 0
        updated = 0
        for lang in ("en", "ne", "hi"):
            if options["lang"] and options["lang"] != lang:
                continue
            entries = self._parse_block(text, lang)
            for key, value in entries.items():
                obj, was_created = UITranslation.objects.get_or_create(
                    key=key, language=lang, defaults={"value": value}
                )
                if was_created:
                    created += 1
                elif options["force"] and obj.value != value:
                    obj.value = value
                    obj.save(update_fields=["value", "updated_at"])
                    updated += 1
            self.stdout.write(f"[{lang}] {len(entries)} keys in bundle")
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created}, updated {updated}."))

    @staticmethod
    def _parse_block(text, lang):
        """Extract "key": "value" pairs from the `const {lang} = {...}` block."""
        start = text.find(f"const {lang} = {{")
        if start < 0:
            return {}
        # Find the matching closing brace by depth counting.
        depth = 0
        end = start
        in_str = None
        escaped = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == in_str:
                    in_str = None
                continue
            if ch in ("'", '"'):
                in_str = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        block = text[start:end + 1]
        entries = {}
        for match in re.finditer(r'"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', block):
            key = match.group(1)
            value = match.group(2).encode().decode("unicode_escape")
            entries[key] = value
        return entries
