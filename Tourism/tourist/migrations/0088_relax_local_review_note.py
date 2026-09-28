"""Let a database that carries local-only columns accept main's writes.

The working database was built on a branch whose migration lineage diverged
from main's: it applied its own 0081-0085, which included
``0085_destinationimage_review_note``. That migration added
``tourist_destinationimage.review_note`` as ``NOT NULL`` with no default, while
main's ``DestinationImage`` model has no such field. Every insert through
main's code therefore failed with::

    IntegrityError: NOT NULL constraint failed: tourist_destinationimage.review_note

so the image-repair and image-fetch commands could not write to it at all.

This migration reconciles that, and nothing else:

* the column is only touched if it actually exists, so a database that never
  took the local-only migration is left alone;
* the column is *kept* and its contents preserved -- it is relaxed to accept
  NULL rather than dropped, because the notes in it are somebody's work;
* a row with no note is given the empty string, so no existing value is lost;
* on any backend that supports ALTER COLUMN the change is a single statement,
  and on SQLite, which does not, the documented table rebuild is used.

The point is to make the column stop being a trap for code that does not know
it exists, without discarding anything.
"""
import re

from django.db import migrations

TABLE = "tourist_destinationimage"
COLUMN = "review_note"


def _columns(connection):
    with connection.cursor() as cursor:
        return [c.name for c in
                connection.introspection.get_table_description(cursor, TABLE)]


def relax(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    if COLUMN not in _columns(connection):
        return

    if vendor != "sqlite":
        # Backends with real ALTER support get a single statement.
        schema_editor.execute(
            f"ALTER TABLE {TABLE} ALTER COLUMN {COLUMN} DROP NOT NULL")
        return

    # SQLite cannot alter a column in place, so the table is rebuilt. The
    # replacement is created from the table's own DDL with the one NOT NULL
    # removed, which keeps the primary key, the CHECK constraints and the
    # foreign keys -- all of which CREATE TABLE ... AS SELECT would discard,
    # leaving every table that points here with an unresolvable reference.
    # Indexes are not part of that DDL, so they are captured and re-created.
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        ddl = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=%s",
            [TABLE]).fetchone()[0]
        index_ddl = [row[0] for row in cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=%s "
            "AND sql IS NOT NULL", [TABLE]).fetchall()]

        patched = re.sub(
            rf'("{COLUMN}"[^,]*?)\s+NOT NULL', r'\1', ddl, count=1)
        if patched == ddl:
            return  # already nullable; nothing to do

        columns = _columns(connection)
        shared = ", ".join(quote(c) for c in columns)
        scratch = quote(f"{TABLE}__relaxed")
        backup = quote(f"{TABLE}__before_relax")

        cursor.execute("PRAGMA foreign_keys=OFF")
        # legacy_alter_table keeps SQLite from rewriting the foreign keys in
        # tourist_destination and tourist_imageembedding to point at the
        # temporary name while the table is renamed.
        cursor.execute("PRAGMA legacy_alter_table=ON")
        cursor.execute(f"DROP TABLE IF EXISTS {backup}")
        cursor.execute(f"ALTER TABLE {quote(TABLE)} RENAME TO {backup}")
        cursor.execute(patched)
        cursor.execute(f"INSERT INTO {quote(TABLE)} ({shared}) "
                       f"SELECT {shared} FROM {backup}")
        cursor.execute(f"DROP TABLE {backup}")
        for statement in index_ddl:
            cursor.execute(statement)
        cursor.execute("PRAGMA legacy_alter_table=OFF")
        cursor.execute("PRAGMA foreign_keys=ON")

        rows = cursor.execute(f"SELECT COUNT(*) FROM {quote(TABLE)}").fetchone()[0]
        violations = cursor.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise RuntimeError(
            f"rebuilding {TABLE} left {len(violations)} foreign key violations")
    _relaxed_rows = rows


def restore(apps, schema_editor):
    """Reversible only as far as re-tightening the constraint.

    Rows that arrived with no note become the empty string, which satisfies
    NOT NULL, so the original constraint can be reinstated.
    """
    connection = schema_editor.connection
    if COLUMN not in _columns(connection):
        return
    schema_editor.execute(
        f"UPDATE {TABLE} SET {COLUMN} = '' WHERE {COLUMN} IS NULL")
    if connection.vendor == "sqlite":
        raise RuntimeError(
            "SQLite cannot reinstate NOT NULL without another table rebuild; "
            "drop the database and rebuild it from the snapshot instead")
    schema_editor.execute(
        f"ALTER TABLE {TABLE} ALTER COLUMN {COLUMN} SET NOT NULL")


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0087_derive_coordinate_accuracy"),
    ]

    operations = [
        migrations.RunPython(relax, restore),
    ]
