# Render PostgreSQL deployment and SQLite data migration

This project uses SQLite by default for local development and PostgreSQL when Render supplies DATABASE_URL. Production uses the existing Render PostgreSQL service named tourism_db.

## 1. Export current SQLite data

From the directory containing manage.py:

    python manage.py check
    python manage.py export_render_data --output data.json
    python -m json.tool data.json > /dev/null

Keep db.sqlite3 as a separate backup until the PostgreSQL import is verified.

The export excludes Django runtime/framework records: content types, permissions, admin log entries, sessions, and JWT blacklist entries.

## 2. Render database connection

render.yaml references the existing tourism_db service:

    DATABASE_URL
      fromDatabase:
        name: tourism_db
        property: connectionString

Render resolves this to the private connection string. Never put the password or actual connection URL in Git. The web service and database should stay in the same region.

## 3. Normal deployment

The Docker image builds the React production bundle and Django static assets. Startup runs:

    python manage.py migrate --noinput

The normal deployment does NOT run loaddata, so deployments cannot accidentally re-import old records.

## 4. One-time import

After the web service deploys successfully and migrations finish, make data.json temporarily available to the service. In Render Shell run:

    python manage.py import_render_data data.json

The command refuses to import unless the active database is PostgreSQL and requires explicit confirmation.

Verify important record counts, Django admin, and API responses.

## 5. After verification

Remove the temporary data.json from Git if it contains production data. The repository ignores data.json and SQLite runtime files.

## Render environment

At minimum configure DEBUG=False, DATABASE_URL (provided from tourism_db), DATABASE_SSL_REQUIRE=true, SECRET_KEY, PUBLIC_SITE_URL, VITE_SITE_URL, CSRF_TRUSTED_ORIGINS, and CORS_ALLOWED_ORIGINS.

Do not set the old SQLite deployment variables DB_ENGINE=sqlite or DB_NAME=/var/lib/tourism/data/db.sqlite3. No Render disk is required for PostgreSQL.

## Media

PostgreSQL stores database records, not uploaded files. The project supports IMAGE_BASE_URL for the large image dataset. If Django-managed uploaded media must survive redeploys, use durable external/object storage or a separate persistent-media strategy.
