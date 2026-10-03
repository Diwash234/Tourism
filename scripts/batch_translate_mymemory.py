"""Batch-translate UI strings via MyMemory free API.

Anonymous: ~5k chars/day. With --email: ~50k chars/day.
Prioritizes top-traffic page prefixes first.

Usage:
    python scripts/batch_translate_mymemory.py --pages navigation,hotelsearch --limit 200
    python scripts/batch_translate_mymemory.py --all --limit 500 --email you@example.com
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.db import transaction  # noqa: E402
from django.db.utils import OperationalError  # noqa: E402

from tourist.models import UITranslation  # noqa: E402

PROGRESS_PATH = ROOT / "scripts" / "translated_ui.json"
PAUSE_SEC = 2.0


def load_missing_keys():
    path = ROOT / "missing_keys.txt"
    pairs = []
    pattern = re.compile(r'\s*"([^"]+)":\s*"((?:[^"\\]|\\.)*)",?\s*$')
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            pairs.append((m.group(1), m.group(2).encode().decode("unicode_escape")))
    return pairs


def mymemory(text, target, email=""):
    params = {"q": text[:450], "langpair": f"en|{target.upper()}"}
    if email:
        params["de"] = email
    r = requests.get("https://api.mymemory.translated.net/get", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("responseStatus") not in (200, "200"):
        raise RuntimeError(f"MyMemory: {data.get('responseDetails')}")
    return (data.get("responseData", {}).get("translatedText") or "").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--lang", default="ne,hi")
    parser.add_argument("--email", default="")
    args = parser.parse_args()

    pairs = load_missing_keys()
    if args.pages:
        prefixes = [p.strip().lower() for p in args.pages.split(",")]
        pairs = [(k, t) for k, t in pairs if k.split(".")[0] in prefixes]
    elif not args.all:
        print("Pass --pages or --all.")
        return
    pairs = pairs[:args.limit]
    print(f"Translating {len(pairs)} keys via MyMemory")

    progress = json.loads(PROGRESS_PATH.read_text(encoding="utf-8")) if PROGRESS_PATH.exists() else {}
    done = 0
    for key, text in pairs:
        for lang in [l.strip() for l in args.lang.split(",")]:
            cache_key = f"{lang}:{key}"
            if cache_key in progress:
                continue
            try:
                translated = mymemory(text, lang, args.email)
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR {key} [{lang}]: {exc}")
                time.sleep(10)
                continue
            if not translated or translated.lower() == text.lower():
                print(f"  SKIP {key} [{lang}]")
                continue
            progress[cache_key] = translated
            # Retry on SQLite lock (another session may be writing).
            for attempt in range(5):
                try:
                    with transaction.atomic():
                        UITranslation.objects.update_or_create(
                            key=key, language=lang, defaults={"value": translated}
                        )
                    break
                except OperationalError:
                    time.sleep(5)
            done += 1
            if done % 20 == 0:
                PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
                print(f"  ... {done} saved")
            time.sleep(PAUSE_SEC)
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
    print(f"Done. {done} new translations.")


if __name__ == "__main__":
    main()
