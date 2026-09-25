# Fresh Pull, Environment Files, Setup and Management Commands

## Pull the current integrated branch

```bash
git fetch --all --prune
git switch arena/01a01013-tourism
git pull --ff-only origin arena/01a01013-tourism
```

If local changes exist:

```bash
git stash push -u -m "before tourism update"
git pull --ff-only origin arena/01a01013-tourism
git stash pop
```

## Environment files

Never commit real keys. Create these local files from templates:

```bash
cp Tourism/.env.example Tourism/.env
cp frontend/Tourism/.env.example frontend/Tourism/.env
cp ml_service/.env.example ml_service/.env
```

Backend keys belong in `Tourism/.env`: image providers, LLM providers, weather/maps, Twilio/Firebase, DHM/BIPAD feeds, routing and image-server settings.

Frontend browser-safe variables belong in `frontend/Tourism/.env` and must use the `VITE_` prefix, for example:

```env
VITE_MAPILLARY_ACCESS_TOKEN=
VITE_IMAGE_BASE_URL=
```

ML configuration belongs in `ml_service/.env`:

```env
HOST=0.0.0.0
PORT=8001
ML_MODEL_PATH=./model
GROQ_API_KEY=
HUGGINGFACE_API_KEY=
```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Tourism/requirements.txt
pip install -r ml_service/requirements.txt
cd frontend/Tourism && npm ci && cd ../..
```

## Database

**The full dataset ships inside the repo.** `Tourism/db.sqlite3` (~54 MB:
8,600+ destinations, 5,000+ hotels, hospital/police/bank directories, route
diagnostics) is committed on purpose — a fresh clone is complete.

Just use the file as-is. **Do not delete it and do not rebuild it with
`manage.py migrate`** — migrate only creates *empty* tables, which is exactly
why a local run "shows no destinations, routes or nearby places".

If you ever deleted or emptied it:

```bash
git checkout -- Tourism/db.sqlite3
```

Rebuilding from scratch (only if you have a real reason — the committed file
is the source of truth) runs the same steps the file was built from:

```bash
cd Tourism
../.venv/bin/python manage.py check
../.venv/bin/python manage.py setup_system
cd ..
```

Manual equivalent:

```bash
cd Tourism
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py import_osm_destinations
../.venv/bin/python manage.py fill_missing_place_coords
../.venv/bin/python manage.py seed_e2e_features
../.venv/bin/python manage.py createsuperuser
cd ..
```

City and coordinate fills also live in `Tourism/dataset/destination_locations.json` (used by `fill_missing_place_coords`). Admin destination edits write both SQLite and that JSON. Missing fields stay empty (`Not recorded` in the UI). Do not run `update_city` — it reverse-geocodes and invents descriptions.

## Run

All services:

```bash
./run_all.sh
```

Or separate terminals:

```bash
cd Tourism && ../.venv/bin/python manage.py runserver 0.0.0.0:8000
```

```bash
cd ml_service && ../.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8001
```

```bash
cd frontend/Tourism && npm run dev -- --host 0.0.0.0 --port 5173
```

Stable production preview:

```bash
cd frontend/Tourism
npm run build
npm run preview -- --host 0.0.0.0 --port 5173
```

## Local self-check (run this when "nothing shows up")

One script verifies the whole local install — database contents, python
dependencies, `manage.py check`, the API on port 8000 (starts it for you if
nothing is running), nearby places/POIs and routes for remote coordinates
(Humla, Jumla, Darchula, Mugu, Taplejung), itineraries, and the frontend
dev-server proxy. Every failure prints the exact fix:

```bash
python scripts/local_check.py
```

Exit code 0 = all green. All common "frontend is empty" symptoms trace to
one of these four causes:

| Symptom in the browser | Cause | Fix |
| --- | --- | --- |
| "connection refused" on every page | Django not running on port 8000 | `cd Tourism && python manage.py runserver 0.0.0.0:8000` (check the traceback if it exits — usually a missing `pip install -r Tourism/requirements.txt`) |
| Pages load but zero destinations / empty map | `db.sqlite3` deleted or freshly migrated (empty tables) | `git checkout -- Tourism/db.sqlite3` then restart runserver |
| White screen / hook errors in console | stale Vite cache | delete `frontend/Tourism/node_modules/.vite` and restart `npm run dev`; hard-refresh the browser |
| 400 from the API in the console | frontend and backend versions out of sync | `git pull` both, restart both servers |

## Data imports and maintenance

Run from `Tourism/` with `../.venv/bin/python manage.py`:

```bash
python manage.py setup_system
python manage.py seed_data
python manage.py seed_taxonomy
python manage.py sync_languages
python manage.py import_dataset
python manage.py import_budget
python manage.py import_risk
python manage.py import_hospital
python manage.py import_police
python manage.py import_hotels
python manage.py import_hotels_csv
python manage.py import_ward_contact
python manage.py import_osm_destinations
python manage.py sync_osm_nepal
python manage.py enrich_nepal_destinations
python manage.py update_city
```

Run imports only when their source files have been reviewed. Most commands are idempotent/update-based, but take a SQLite backup first.

## Image and gallery commands

```bash
python manage.py import_images
python manage.py attach_local_photos
python manage.py fetch_destination_images
python manage.py backfill_destination_images
python manage.py assign_destination_photos
python manage.py reassign_covers
python manage.py export_media
python manage.py import_media
python manage.py download_district_gallery --output ../frontend/Tourism/public/images/destinations/districts
```

AI generation commands require provider configuration and must remain labeled AI-generated:

```bash
python manage.py generate_destination_images
python manage.py generate_all_images
python manage.py download_ai_images
```

## Discovery and quality

```bash
python manage.py run_destination_discovery
python manage.py add_missing_destinations
python manage.py add_more_destinations
python manage.py expand_destinations
python manage.py categorize_existing
python manage.py audit_data_quality --output ../reports/data-gaps.csv
python manage.py acceptance_check_nepal
```

## Risk and official feeds

```bash
python manage.py ingest_risk_feed /path/to/feed.json --provider dhm --verified
python manage.py sync_official_risk --provider all --dry-run
python manage.py sync_official_risk --provider all
```

Do not use `--verified` for an unconfirmed source.

## ML preparation

```bash
python manage.py backfill_embeddings
```

Training is available from Admin Dashboard → Community Services & ML, or via the whitelisted admin pipeline API. Review exported rows and validation output before deployment.

## Validation

```bash
cd Tourism
../.venv/bin/python manage.py check
../.venv/bin/python manage.py test tourist.tests.RecommendationAndRiskArchitectureTests
cd ../frontend/Tourism
npm run build
```

## Backup before bulk changes

```bash
mkdir -p backups
sqlite3 Tourism/db.sqlite3 ".backup 'backups/tourism-$(date +%Y%m%d-%H%M%S).sqlite3'"
```

Also back up `Tourism/media/`, generated image folders and model artifacts.
