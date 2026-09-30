# Supplements 0095_render_schema_sync with the two schema changes that
# migration does not cover.
#
# 1. GPS fix-quality columns on tourist_user. 0083_user_gps_fix_quality created
#    them with raw SQL inside a RunPython, which changes the database but not
#    the migration state - so Django has no record of them and every later
#    `makemigrations` wants to add them again. Creating them twice would fail,
#    so the database side below only fills in whatever is still missing while
#    the state side always records the fields.
# 2. Hotel.website grew to 600 characters (long partner URLs), which
#    0095_render_schema_sync does not record.

from django.db import migrations, models

GPS_USER_COLUMNS = (
    # (column, PostgreSQL type, SQLite type, modifiers)
    ("gps_accuracy_m", "double precision", "real", "NULL"),
    ("gps_recorded_at", "timestamp with time zone", "datetime", "NULL"),
    ("gps_validated_at", "timestamp with time zone", "datetime", "NULL"),
    ("gps_validation_reasons", "jsonb", "text", "NOT NULL DEFAULT '[]'"),
    ("gps_validation_state", "character varying(20)", "varchar(20)", "NOT NULL DEFAULT ''"),
)


def _column_exists(connection, table, column):
    """True when the column is present, using Django's vendor-neutral introspection."""
    with connection.cursor() as cursor:
        try:
            described = connection.introspection.get_table_description(cursor, table)
        except Exception:  # table not created yet
            return False
    return any(getattr(col, "name", None) == column for col in described)


def add_missing_gps_columns(apps, schema_editor):
    """Create any GPS columns that are absent; leave existing ones untouched."""
    connection = schema_editor.connection
    for name, postgres_type, sqlite_type, modifiers in GPS_USER_COLUMNS:
        if _column_exists(connection, "tourist_user", name):
            continue
        column_type = postgres_type if connection.vendor == "postgresql" else sqlite_type
        schema_editor.execute(
            'ALTER TABLE "tourist_user" ADD COLUMN "%s" %s %s' % (name, column_type, modifiers)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0095_render_schema_sync"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Create only the GPS columns that are genuinely missing (see
            # GPS_USER_COLUMNS above), but always record them in the state so
            # `makemigrations --check` stays clean.
            database_operations=[
                migrations.RunPython(add_missing_gps_columns, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="user",
                    name="gps_accuracy_m",
                    field=models.FloatField(blank=True, help_text="Device-reported accuracy in metres", null=True),
                ),
                migrations.AddField(
                    model_name="user",
                    name="gps_recorded_at",
                    field=models.DateTimeField(blank=True, help_text="When the device took the fix", null=True),
                ),
                migrations.AddField(
                    model_name="user",
                    name="gps_validated_at",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="user",
                    name="gps_validation_reasons",
                    field=models.JSONField(blank=True, default=list),
                ),
                migrations.AddField(
                    model_name="user",
                    name="gps_validation_state",
                    field=models.CharField(blank=True, help_text="precise / approximate / unusable", max_length=20),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="hotel",
            name="website",
            field=models.URLField(blank=True, max_length=600),
        ),
    ]
