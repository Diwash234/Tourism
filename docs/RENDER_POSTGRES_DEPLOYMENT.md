# Render Deployment — PostgreSQL variant

**Read this alongside `RENDER_SQLITE_DEPLOYMENT.md`.** That guide is the
default path committed in this repo (Docker image + SQLite on a Render Disk,
driven by `render.yaml` and `scripts/render_start.sh`).

This document covers the other option: **PostgreSQL as the production
database**, for when SQLite's single-writer limitation is the binding
constraint. The application code supports both with no change to the
topology — `DATABASE_URL` selects PostgreSQL when present, and absent that it
stays on SQLite.

```
OPTION A (default, already implemented)
  Docker image  ->  SQLite  ->  Render Disk  (/var/lib/tourism)

OPTION B (this document)
  Docker/WSGI   ->  PostgreSQL  (Render managed, via DATABASE_URL)
```

---

## Switching from Option A to Option B

`render.yaml` currently pins SQLite:

```yaml
- key: DB_ENGINE
  value: "sqlite"
- key: DB_NAME
  value: "/var/lib/tourism/data/db.sqlite3"
```

`DATABASE_URL` is checked **before** `DB_ENGINE`, so adding it is enough to
take effect — but leaving the SQLite keys in place is misleading, and the disk
then serves no purpose. Remove both keys and the `disk:` block, and add:

```yaml
- key: DATABASE_URL
  fromDatabase:
    name: tourism_db
    property: connectionString
- key: CONN_MAX_AGE
  value: "600"
```

`fromDatabase` makes Render inject the **internal** database URL, so the
credential never appears in the repository. Set `DATABASE_SSLMODE=require`
only if you point at the *external* URL.

---

## Environment variables

Required:

| Key | Value |
|---|---|
| `DATABASE_URL` | internal URL for `tourism_db` (or use `fromDatabase` in `render.yaml`) |
| `SECRET_KEY` | generate — `render.yaml` already does this |
| `DEBUG` | `False` |
| `PUBLIC_SITE_URL` | your site URL (used for `FRONTEND_URL`/`BACKEND_URL` fallbacks) |

`ALLOWED_HOSTS` defaults to **empty** in this project, not `*`. Render
populates `RENDER_EXTERNAL_HOSTNAME` automatically and it is appended to both
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, so the default deployment needs no
host configuration. Set `ALLOWED_HOSTS` yourself only when serving a custom
domain.

Optional:

| Key | Value | Purpose |
|---|---|---|
| `DATABASE_SSLMODE` | `require` | external URL only; the internal URL must **not** use it |
| `CONN_MAX_AGE` | `600` | reuse DB connections between requests |

---

## One-time data transfer

SQLite is the source, PostgreSQL the destination. They are never connected.

### Export

`dumpdata` writes its output file using the **locale** codec. On Windows that
is cp1252, and this dataset contains Devanagari, so the plain command fails
with `Unable to serialize database: 'charmap' codec can't encode characters`
and leaves a 0-byte file. UTF-8 mode is required:

```powershell
cd Tourism
$env:PYTHONUTF8="1"
python manage.py dumpdata --natural-foreign --natural-primary -o data.json
```

Verified: 97.6 MB, valid JSON, 92,973 objects.

For a production import, leave the operational tables behind — audit logs,
revoked JWTs, live sessions, routing diagnostics, the notification queue and
ML embeddings have no business in a new production database:

```powershell
python manage.py dumpdata --natural-foreign --natural-primary `
  -e audit -e sessions -e token_blacklist -e navigation.routediagnostics `
  -e chatbot.chatmessage -e tourist.notification -e tourist.imageembedding `
  -e admin -o data.json
```

Verified: 82.1 MB. Contents confirmed: 8,757 destinations, 26,106 destination
images, 5,027 hotels, 491 hospitals, 958 police stations, 77 districts, 46
categories, 21 users.

### Import

`data.json` is a complete copy of the database **including user password
hashes**. It is git-ignored and must not be committed. Run `loaddata` from your
own machine against the **external** URL so the data never enters git at all:

```powershell
$env:DATABASE_URL = "postgresql://USER:PASSWORD@EXTERNAL_HOST:5432/DBNAME"
$env:DATABASE_SSLMODE = "require"
python manage.py loaddata data.json
Remove-Item Env:DATABASE_URL, Env:DATABASE_SSLMODE
```

Your local `db.sqlite3` is untouched — the variable only redirects Django for
that one command.

Run it **once**. A second `loaddata` re-inserts and fails on primary keys, so
it must not go into the build command.

---

## Verify

```bash
python manage.py check --deploy     # production posture
python manage.py showmigrations
```

Then confirm the data landed:

```bash
python manage.py shell -c "
from tourist.models import Destination, DestinationImage, Hotel
from django.contrib.auth import get_user_model
print('destinations', Destination.objects.count())
print('images      ', DestinationImage.objects.count())
print('hotels      ', Hotel.objects.count())
print('users       ', get_user_model().objects.count())
"
```

Expected: `8757`, `26106`, `5027`, `21`.

```bash
curl -I https://your-service.onrender.com/health/
```

---

## Notes on the schema

`migrate` against an empty database was verified end to end: **138 migrations,
134 tables, no errors**, including the 30 `RunPython` data migrations. There is
no `RunSQL` and no Postgres-only ORM usage (`contrib.postgres`, `ArrayField`,
`raw()`), so the chain is portable. It has not been run against a real
PostgreSQL instance — do that once on a scratch database first.

---

## Gotchas

* **Free PostgreSQL databases expire.** Check Render's current free-tier terms.
* **A second writer is only safe on PostgreSQL.** SQLite serialises writers;
  that is the reason to move. Do not point two services at one SQLite file.
* **`MEDIA_ROOT` is ephemeral** unless backed by the Render Disk in
  `render.yaml`. Uploaded CMS media is lost on redeploy otherwise.
* **`check --deploy` reports ~300 `drf_spectacular` warnings.** These are
  schema type-hint hints, not security findings.
* `STATICFILES_DIRS` points at `frontend_dist`, which only exists after the
  Docker build copies the Vite bundle. `staticfiles.W004` is expected locally.
