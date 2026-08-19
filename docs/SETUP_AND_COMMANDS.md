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
pip install -r Tourism/requirement.txt
pip install -r ml_service/requirements.txt
cd frontend/Tourism && npm ci && cd ../..
```

## Database

```bash
cd Tourism
../.venv/bin/python manage.py check
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py createsuperuser
cd ..
```

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
