"""Seed EN UITranslation rows from missing_keys.txt."""
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

from tourist.models import UITranslation

pairs = []
pattern = re.compile(r'\s*"([^"]+)":\s*"((?:[^"\\]|\\.)*)",?\s*$')
for line in (ROOT / "missing_keys.txt").read_text(encoding="utf-8").splitlines():
    m = pattern.match(line)
    if m:
        pairs.append((m.group(1), m.group(2).encode().decode("unicode_escape")))

created = 0
for key, text in pairs:
    _, was = UITranslation.objects.get_or_create(key=key, language="en", defaults={"value": text})
    if was:
        created += 1
print(f"{len(pairs)} keys parsed, {created} new EN rows")
