"""Batch-translate missing UI strings via the backend translation engine.

Usage:
    python scripts/batch_translate_ui.py --pages Landing,DestinationList,Emergency
    python scripts/batch_translate_ui.py --all --limit 500
    python scripts/batch_translate_ui.py --pages Landing --lang ne

Reads missing_keys.txt (key = english text lines), translates each to
ne/hi, and appends results to the i18n bundle + upserts UITranslation rows.
Progress is saved incrementally to translated_ui.json so interrupted runs resume.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")  # relative db.sqlite3 resolves from the Django project dir
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from django.db import transaction

from tourist.models import UITranslation

# Import after django.setup so settings are configured.
sys.path.insert(0, str(ROOT / "Tourism" / "translation"))
from engine import translate_text  # noqa: E402

I18N_PATH = ROOT / "frontend" / "Tourism" / "src" / "i18n" / "index.js"
PROGRESS_PATH = ROOT / "scripts" / "translated_ui.json"


def load_missing_keys():
    path = ROOT / "missing_keys.txt"
    if not path.exists():
        print("missing_keys.txt not found. Run extract_ui_strings.py --add-missing first.")
        return []
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*"([^"]+)":\s*"((?:[^"\\]|\\.)*)",?\s*$', line)
        if m:
            key = m.group(1)
            text = m.group(2).encode().decode("unicode_escape")
            pairs.append((key, text))
    return pairs


def load_progress():
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {}


def save_progress(data):
    PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", default="", help="comma-separated page prefixes (e.g. landing,destination)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--lang", default="ne,hi")
    args = parser.parse_args()

    pairs = load_missing_keys()
    print(f"Loaded {len(pairs)} keys from missing_keys.txt")
    if args.pages:
        prefixes = [p.strip().lower() for p in args.pages.split(",")]
        pairs = [(k, t) for k, t in pairs if k.split(".")[0] in prefixes]
        print(f"Filtered to {len(pairs)} keys for pages {prefixes}")
    elif not args.all:
        print("Pass --pages or --all.")
        return

    langs = [l.strip() for l in args.lang.split(",")]
    progress = load_progress()
    pairs = pairs[:args.limit]

    done = 0
    for key, text in pairs:
        for lang in langs:
            cache_key = f"{lang}:{key}"
            if cache_key in progress:
                continue
            try:
                translated = translate_text(text, lang, "en", provider="standard")
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR {key} [{lang}]: {exc}")
                continue
            if not translated or translated == text:
                print(f"  SKIP {key} [{lang}]: no translation returned")
                continue
            progress[cache_key] = translated
            with transaction.atomic():
                UITranslation.objects.update_or_create(
                    key=key, language=lang, defaults={"value": translated}
                )
            done += 1
            if done % 10 == 0:
                save_progress(progress)
                print(f"  ... {done} saved")
    save_progress(progress)
    print(f"Done. {done} new translations saved.")


if __name__ == "__main__":
    main()
