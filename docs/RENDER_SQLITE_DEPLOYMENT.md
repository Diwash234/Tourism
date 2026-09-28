# Render deployment — React + Django + SQLite

This repository is prepared for a single Render Docker web service.

## Architecture

- React/Vite is built during the Docker image build.
- The built React files are copied into Django's static collection.
- Django serves the API and the React application from the same origin.
- SQLite remains the Django database.
- Render Persistent Disk stores the SQLite database and uploaded media.

## Render service

Use the repository's `render.yaml` Blueprint, or create a Docker Web Service manually.

Required environment values:

- `DEBUG=False`
- `SECRET_KEY`: generate a secret
- `DB_ENGINE=sqlite`
- `DB_NAME=/var/lib/tourism/data/db.sqlite3`
- `MEDIA_ROOT=/var/lib/tourism/media`
- `PUBLIC_SITE_URL=https://YOUR-RENDER-DOMAIN.onrender.com`
- `VITE_SITE_URL=https://YOUR-RENDER-DOMAIN.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://YOUR-RENDER-DOMAIN.onrender.com`
- `CORS_ALLOWED_ORIGINS=https://YOUR-RENDER-DOMAIN.onrender.com`

Set `IMAGE_BASE_URL` only if the large destination image dataset is hosted separately. Do not point it at localhost in production.

## Important SQLite requirement

The Render Persistent Disk is required. Without persistent storage, SQLite data and uploaded media can disappear when the service is replaced or restarted.

The Blueprint mounts the disk at:

`/var/lib/tourism`

with:

- database: `/var/lib/tourism/data/db.sqlite3`
- media: `/var/lib/tourism/media`

## First deployment

The container automatically runs:

`python manage.py migrate --noinput`

before Gunicorn starts.

After the first deploy, create the Django admin account from the Render Shell:

`cd /app/Tourism && python manage.py createsuperuser`

Do not put admin passwords in Git or in `render.yaml`.

## React/API

Because React and Django share the same Render origin, the production frontend can use the same-origin `/api/v1` API path. This avoids a separate frontend CORS deployment.

## Images

The repository deliberately keeps the large image dataset outside Git. If destination images are hosted by the project's image server/CDN, set `IMAGE_BASE_URL` to its HTTPS public URL.

## Before calling deployment complete

Verify:

1. Render build succeeds.
2. `/health/` returns HTTP 200.
3. `/api/v1/health/` returns HTTP 200.
4. React home page loads.
5. Login works.
6. Django admin/CMS works.
7. SQLite migrations complete.
8. A CMS edit persists after a service restart.
9. Uploaded media persists after a restart.
10. Destination image URLs resolve from the configured image host.
