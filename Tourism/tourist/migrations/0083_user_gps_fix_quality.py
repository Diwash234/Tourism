from django.db import migrations


class Migration(migrations.Migration):
    """GPS fix quality on the user.

    This migration originally created the ``gps_*`` columns with raw SQL inside a
    ``RunPython``. That updates the database but never touches the migration
    state, so Django kept "discovering" the same five fields on every later
    ``makemigrations`` run. The raw SQL was also unsafe: it queried the
    Postgres-only ``information_schema`` (SQLite has no such table) and called
    ``schema_editor.add_field(model=..., field=..., name=...)`` with a ``name``
    keyword the API does not accept, so a database that did not already have the
    columns failed outright.

    Column creation now happens in ``0095_webhookendpoint_and_more``, which
    creates anything still missing *and* records the fields in the migration
    state in the same operation. This migration is therefore intentionally empty;
    it is kept so its number stays reserved in the migration graph.
    """

    dependencies = [
        ('tourist', '0082_destinationimage_review_provenance'),
    ]

    operations = []
