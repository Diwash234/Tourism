import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Tourism"))
os.chdir(ROOT / "Tourism")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django

django.setup()

from tourist.models import TravelGuide

fixed = 0
for g in TravelGuide.objects.all():
    if "duplicate-source-name" in g.slug:
        new_slug = g.slug.replace("-duplicate-source-name", "")
        # Ensure uniqueness
        if not TravelGuide.objects.filter(slug=new_slug).exclude(pk=g.pk).exists():
            g.slug = new_slug
            g.save(update_fields=["slug"])
            fixed += 1
            print(f"Fixed: {g.slug}")

print(f"\nTotal fixed: {fixed}")
