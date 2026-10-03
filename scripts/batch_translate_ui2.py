"""Batch-translate missing UI strings using deep-translator batch mode.

Google allows ~5 req/sec. This sends texts in batches of 20 with a
2-second pause between batches, and resumes from translated_ui.json.

Usage:
    python scripts/batch_translate_ui2.py --pages landing,destinationdetails --limit 800
    python scripts/batch_translate_ui2.py --all --limit 2000
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

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

PROGRESS_PATH = ROOT / "scripts" / "translated_ui.json"
BATCH_SIZE = 20
PAUSE_SEC = 2


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

    if GoogleTranslator is None:
        print("deep-translator not installed")
        return

    pairs = load_missing_keys()
    if args.pages:
        prefixes = [p.strip().lower() for p in args.pages.split(",")]
        pairs = [(k, t) for k, t in pairs if k.split(".")[0] in prefixes]
    elif not args.all:
        print("Pass --pages or --all.")
        return
    pairs = pairs[:args.limit]
    print(f"Translating {len(pairs)} keys")

    progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8")) if PROGRESS_PATH.exists() else {}

    for lang in [l.strip() for l in args.lang.split(",")]:
        translator = GoogleTranslator(source="en", target=lang)
        pending = [(k, t) for k, t in pairs if f"{lang}:{k}" not in progress]
        print(f"[{lang}] {len(pending)} pending")
        for i in range(0, len(pending), BATCH_SIZE):
            chunk = pending[i:i + BATCH_SIZE]
            texts = [t for _, t in chunk]
            try:
                results = translator.translate_batch(texts)
            except Exception as exc:  # noqa: BLE001
                print(f"  batch {i//BATCH_SIZE} failed: {exc}")
                time.sleep(10)
                continue
            with transaction.atomic():
                for (key, _), translated in zip(chunk, results):
                    if translated and translated.strip():
                        progress[f"{lang}:{key}"] = translated
                        UITranslation.objects.update_or_create(
                            key=key, language=lang, defaults={"value": translated}
                        )
            # Save progress incrementally.
            PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
            print(f"  [{lang}] {min(i + BATCH_SIZE, len(pending))}/{len(pending)}")
            time.sleep(PAUSE_SEC)

    print("Done.")


if __name__ == "__main__":
    main()
