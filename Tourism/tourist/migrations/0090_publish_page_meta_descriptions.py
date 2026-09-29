"""Carry the 0088 page descriptions into the *published* page snapshots.

0088 replaced the auto-generated descriptions ("<Title> on the Nepal Yatra"
and the old home slogan) in ``ManagedPage.meta_description``. The public
config, however, serves ``published_snapshot`` (draft edits never reach the
public until Publish), so visitors and search engines still saw the old text.

Same guard as 0088: only snapshot descriptions that are still exactly the
generated text, the old slogan, or empty are replaced. Anything an editor
published is left alone.
"""
import importlib

from django.db import migrations

_0088 = importlib.import_module("tourist.migrations.0088_page_meta_descriptions")
DESCRIPTIONS = _0088.DESCRIPTIONS
LEGACY_HOME = _0088.LEGACY_HOME


def forwards(apps, schema_editor):
    ManagedPage = apps.get_model("tourist", "ManagedPage")
    for page in ManagedPage.objects.filter(route__in=DESCRIPTIONS.keys()):
        snap = page.published_snapshot
        if not isinstance(snap, dict) or not snap:
            continue
        current = snap.get("meta_description") or ""
        generated = {f"{title} on the Nepal Yatra" for title in (snap.get("title"), page.title) if title}
        if current in generated or current in (LEGACY_HOME, ""):
            snap = dict(snap)
            snap["meta_description"] = DESCRIPTIONS[page.route][:320]
            page.published_snapshot = snap
            page.save(update_fields=["published_snapshot"])


class Migration(migrations.Migration):
    dependencies = [("tourist", "0089_dedupe_hero_slides")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
