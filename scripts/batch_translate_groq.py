"""Batch-translate missing UI strings via Groq (fast, generous free tier).

Uses the backend translation engine with provider="groq" so no Google
rate limits apply. Resumes from translated_ui.json.

Usage:
    python scripts/batch_translate_groq.py --pages landing,destinationdetails --limit 500
    python scripts/batch_translate_groq.py --all --limit 2000
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.db import transaction  # noqa: E402

from tourist.models import UITranslation  # noqa: E402

sys.path.insert(0, str(ROOT / "Tourism" / "translation"))
from engine import translate_text  # noqa: E402

PROGRESS_PATH = ROOT / "scripts" / "translated_ui.json"
PAUSE_SEC = 1.0


def load_missing_keys():
    path = ROOT / "missing_keys.txt"
    pairs = []
    pattern = re.compile(r'\s*"([^"]+)":\s*"((?:[^"\\]|\\.)*)",?\s*$')
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            pairs.append((m.group(1), m.group(2).encode().decode("unicode_escape")))
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--lang", default="ne,hi")
    args = parser.parse_args()

    pairs = load_missing_keys()
    if args.pages:
        prefixes = [p.strip().lower() for p in args.pages.split(",")]
        pairs = [(k, t) for k, t in pairs if k.split(".")[0] in prefixes]
    elif not args.all:
        print("Pass --pages or --all.")
        return
    pairs = pairs[:args.limit]
    print(f"Translating {len(pairs)} keys via Groq")

    progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8")) if PROGRESS_PATH.exists() else {}
    done = 0
    for key, text in pairs:
        for lang in [l.strip() for l in args.lang.split(",")]:
            cache_key = f"{lang}:{key}"
            if cache_key in progress:
                continue
            try:
                translated = translate_text(text, lang, "en", provider="groq")
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR {key} [{lang}]: {exc}")
                time.sleep(5)
                continue
            if not translated or translated.strip() == text.strip():
                print(f"  SKIP {key} [{lang}]")
                continue
            progress[cache_key] = translated
            with transaction.atomic():
                UITranslation.objects.update_or_create(
                    key=key, language=lang, defaults={"value": translated}
                )
            done += 1
            if done % 20 == 0:
                PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
                print(f"  ... {done} saved")
            time.sleep(PAUSE_SEC)
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
    print(f"Done. {done} new translations.")


if __name__ == "__main__":
    main()
