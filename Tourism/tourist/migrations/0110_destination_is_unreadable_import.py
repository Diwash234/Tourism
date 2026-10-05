"""Backfill Destination.is_unreadable_import from the regex it now caches.

Every public read query filters on this column, so it must be correct for all
existing rows the moment the column appears -- otherwise previously-hidden
import garbage would briefly become public. The forward data function and the
reverse one are both idempotent and use ``save(update_fields=...)`` so nothing
else on the row is touched.
"""

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Populate the flag from the current name of every destination."""
    Destination = apps.get_model("tourist", "Destination")
    # Historical model: the classmethods/helpers added to the real model are not
    # available here, so the rule is restated exactly (and covered by
    # test_is_unreadable_import_name_matches_the_cached_rule).
    import re

    unreadable = re.compile("[\u4e00-\u9fff\uac00-\ud7af]")
    readable = re.compile("[A-Za-z\u0900-\u097f]")

    db_alias = schema_editor.connection.alias
    rows = Destination.objects.using(db_alias).only("id", "name").iterator(chunk_size=2000)

    to_update = []
    for row in rows:
        name = row.name or ""
        flag = bool(unreadable.search(name) and not readable.search(name))
        if flag:
            row.is_unreadable_import = True
            to_update.append(row)
            if len(to_update) >= 1000:
                Destination.objects.using(db_alias).bulk_update(
                    to_update, ["is_unreadable_import"]
                )
                to_update = []
    if to_update:
        Destination.objects.using(db_alias).bulk_update(
            to_update, ["is_unreadable_import"]
        )


def backwards(apps, schema_editor):
    """Nothing to undo: the flag is derived data, and the column is dropped."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0109_alter_currenthazard_hazard_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="destination",
            name="is_unreadable_import",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text=(
                    "True when the name is unreadable import garbage (CJK/Hangul only, "
                    "no Latin or Devanagari letters). Maintained automatically by save(); "
                    "use the recompute_unreadable_import_names command after a bulk import."
                ),
            ),
        ),
        migrations.AddIndex(
            model_name="destination",
            index=models.Index(
                fields=["is_active", "status", "is_unreadable_import", "-created_at"],
                name="tourist_dest_public_idx",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
