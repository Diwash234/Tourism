# 🇳🇵 Digital Nepal Tourism Platform — Master Build, Train & Run Guide

Welcome to the **Digital Nepal Tourism Platform**, an autonomous, AI-driven, multi-modal travel recommendation, real-time safety, navigation, and budget estimation platform for Nepal's 7 Provinces, 77 Districts, and 753 Municipalities.

---

## 🏛️ System Architecture Diagram

```
       [ Client Browser / Mobile ]
                   │
                   ▼  HTTP / Vite Proxy (Port 5173)
       ┌───────────────────────────┐
       │   Vite 6 React Frontend   │  (714 SPA Modules)
       └─────────────┬─────────────┘
                     │  REST API (/api/v1/*)
                     ▼  (Port 8000)
       ┌───────────────────────────┐
       │   Django 5.0.6 REST API   │  (Business Logic, Auth, RBAC, Provenance, SQLite DB)
       └─────────────┬─────────────┘
                     │  Internal Microservice Calls (Port 8001)
                     ▼
       ┌───────────────────────────┐
       │  FastAPI ML Microservice  │  (TF-IDF, Random Forest, NetworkX Graph, Translation)
       └───────────────────────────┘
```

---

## ⚡ Quickstart: One-Command System Launch

You can launch the entire stack (Dependencies ➔ ML Verification ➔ DB Migrations ➔ SPA Build ➔ All 3 Servers) with a single command:

```bash
chmod +x run_all.sh
./run_all.sh
```

Once running, your live endpoints are:
- 🌐 **Frontend SPA Website**: `http://0.0.0.0:5173`
- ⚙️ **Django Backend REST API**: `http://0.0.0.0:8000`
- 🧠 **FastAPI ML Microservice**: `http://0.0.0.0:8001`

---

## 📑 Manual Step-by-Step Execution Guide (From First to Last)

Follow these steps to set up, train ML models, seed data, run tests, and launch each component manually.

### 🐍 Phase 1: Environment Setup & Python Requirements

1. **Verify Python & Node.js versions**:
   ```bash
   python3 --version  # Requires Python 3.10+
   node --version     # Requires Node.js 18+
   ```
2. **Install Python dependencies**:
   ```bash
   python3 -m pip install -r Tourism/requirement.txt -r ml_service/requirements.txt --break-system-packages
   ```
3. **Configure optional environment variables**:
   ```bash
   cp Tourism/.env.example Tourism/.env
   ```

---

### 🧠 Phase 2: Machine Learning Model Training & Microservice (`ml_service/`)

The ML microservice provides destination recommendation scoring, budget regression, safety analysis, sequence translation, and 77-district highway routing.

1. **Navigate to `ml_service/`**:
   ```bash
   cd ml_service
   ```
2. **Clean and preprocess raw datasets**:
   ```bash
   python3 training/clean_risk.py
   python3 training/processed_data/clean_destinations.py
   python3 training/processed_data/clean_budget.py
   ```
3. **Train all machine learning models**:
   ```bash
   # 1. Train recommendation TF-IDF vectorizer & similarity matrix
   python3 training/train_recommendation_model.py

   # 2. Train Random Forest risk regressor & classifier
   python3 training/train_risk_model.py

   # 3. Train Random Forest travel budget estimator
   python3 training/train_budget_model.py

   # 4. Train multi-lingual translation model
   python3 training/train_translation_model.py

   # 5. Build 5,764-node / 37,055-edge Nepal highway & trekking route graph
   python3 training/build_route_graph.py
   ```
4. **Verify generated model artifacts**:
   ```bash
   python3 check_model.py
   ```
5. **Start the FastAPI ML microservice on port 8001**:
   ```bash
   python3 -m uvicorn app:app --host 0.0.0.0 --port 8001
   ```

---

### 🗄️ Phase 3: Django Backend Setup, Migrations & Data Seeding (`Tourism/`)

The Django backend manages user accounts, RBAC roles (`admin`, `staff`, `local`, `user`), destination catalogs, emergency services, and multi-source image provenance.

1. **Navigate to `Tourism/`**:
   ```bash
   cd Tourism
   ```
2. **Apply database migrations**:
   ```bash
   python3 manage.py migrate
   ```
3. **Seed and enrich the database** (populates 6,414 destinations, hospitals, police stations, hotels, and emergency contacts):
   ```bash
   python3 manage.py seed_data
   python3 manage.py enrich_nepal_destinations
   python3 manage.py import_hospital
   python3 manage.py import_police
   python3 manage.py import_hotels
   python3 manage.py import_risk
   ```
4. **Run the automated backend test suite** (verifies 79/79 automated tests pass):
   ```bash
   python3 manage.py test --noinput
   ```
5. **Start the Django development server on port 8000**:
   ```bash
   python3 manage.py runserver 0.0.0.0:8000
   ```

---

### ⚛️ Phase 4: Vite React Frontend SPA Setup & Build (`frontend/Tourism/`)

1. **Navigate to `frontend/Tourism/`**:
   ```bash
   cd frontend/Tourism
   ```
2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```
3. **Verify the production build** (compiles 714 modules to `/dist`):
   ```bash
   npm run build
   ```
4. **Start the live Vite development server on port 5173**:
   ```bash
   npm run dev -- --host 0.0.0.0 --port 5173
   ```

---

### 🖼️ Phase 5: Multi-Source Image Acquisition Pipeline & Usage-Rights Auditor

The system includes an automated 12-stage Waterfall Provider Chain (`Wikimedia Commons` ➔ `Openverse` ➔ `OSM/Mapillary` ➔ `Nepal Gov Open Data` ➔ `Satellite Terrain` ➔ `Unsplash` ➔ `Pexels` ➔ `Flickr` ➔ `Pixabay` ➔ `Kaggle Seeds` ➔ `AI Illustration Fallback`) with a strict **Google Usage-Rights Commercial License Auditor** (`verify_commercial_license`).

#### API Endpoints:
- **List Discovered Images**:
  ```bash
  curl -X GET http://0.0.0.0:8000/api/v1/destinations/phewa-lake-tal-barahi/images/
  ```
- **Trigger Automated Multi-Source Discovery**:
  ```bash
  curl -X POST http://0.0.0.0:8000/api/v1/destinations/phewa-lake-tal-barahi/images/discover/
  ```
- **Force Refresh Image Collection**:
  ```bash
  curl -X POST http://0.0.0.0:8000/api/v1/destinations/phewa-lake-tal-barahi/images/refresh/
  ```

#### Admin Dashboard Desk:
In the web application, log in as an administrator and go to the **Admin Dashboard ➔ `"🖼️ Multi-Source Image Pipeline"`** tab to inspect provider breakdown counts, view license verification badges (`✓ CC Commercial Reusable`), and launch automated discovery across any destination.

---

## 🧪 System Verification Summary

- **Automated Test Suite**: `79 / 79` Django automated tests passing (`OK`).
- **Frontend Bundle**: `714 / 714` Vite modules compiled with `0 errors`.
- **Database Status**: 6,414 verified destinations, 7,238 verified media records, 479 hospitals across all 77 districts, 1,058 police stations, and 1,552 hotels.

---

## 🔐 Authentication Portals & Roles

The app ships three visually distinct login pages so travellers, staff and
administrators never see the same generic form:

| Portal | URL | Who can log in | How accounts are created |
|---|---|---|---|
| Traveller | `/login` | registered tourists | public **Sign Up** at `/register` |
| Staff | `/staff/login` | staff, moderators, district managers, hotel managers, tourist police | created by an admin with `python manage.py create_staff` |
| Admin | `/admin/login` | `is_staff`/`is_superuser`/admin roles | created on the server with `python manage.py createsuperuser` |

- Super-admins are **only** created via `python manage.py createsuperuser` (Django backend), never through the public sign-up form.
- Staff accounts are provisioned with:
  ```bash
  python manage.py create_staff \
      --email staff@tourism.gov.np \
      --first-name Staff --last-name Member \
      --role content_moderator
  ```
- The admin `/staff` page is guarded by `StaffRoute` and `/admin` by `AdminRoute`; unauthenticated users are redirected to the matching login portal.

## 🖼️ Real, Diverse Destination Images

Image URLs stored in the database are served correctly even when they point
to external hosts (Unsplash/Wikimedia). The serializer detects `http(s)://`
values and returns them verbatim instead of mangling them into broken
`/media/https%3A/...` links.

Assign diverse, category-relevant, openly-licensed cover + gallery images
to every destination:

```bash
cd Tourism
python manage.py assign_destination_photos            # curated catalog (offline-safe)
python manage.py assign_destination_photos --live      # also query Wikimedia Commons (needs internet)
python manage.py assign_destination_photos --hotels-only
```

- Each destination receives ~10 varied photos with provenance (author,
  license, source URL) stored in `DestinationImage`.
- The old solid purple "imgN.jpg" placeholder blocks are no longer used by
  the frontend or stored as gallery images.
- Images come from the Unsplash License / CC BY / CC BY-SA pool; non-commercial
  (CC BY-NC) and all-rights-reserved items are rejected by the license
  auditor in `image_acquisition_pipeline.py`.
- Admins can refresh and roll back cover images:
  - `POST /api/v1/destinations/<slug>/images/discover/`
  - `POST /api/v1/destinations/<slug>/images/refresh/`
  - `POST /api/v1/destinations/<slug>/images/<image_id>/set-cover/`  (rollback / manual override)

## 💰 CSV-Driven Budget Estimator

The budget estimator reads real Nepal travel-cost data from
`ml_service/processed_data/budget_features.csv` (2,200+ destinations, 195
districts) and parses range cells like `"40-120"` into midpoint baselines.
Numeric trip inputs (e.g. 3 or 4 days / travellers) are accepted directly;
the response includes `"baseline_source": "dataset_csv"` and the dataset
coverage so the UI can show that the estimate is data-backed.

---

## 🖼️ Standalone Image Server (100k+ images, NOT in Git)

The large tourism image dataset is served from a **separate static image server**;
Django stores only paths + metadata and the browser loads images directly from
the image server.

- **Docs:** [docs/IMAGE_SERVER.md](docs/IMAGE_SERVER.md) and [image-server/README.md](image-server/README.md)
- **Local dev:** `cd image-server && python -m http.server 8000`
- **Import metadata:** `python manage.py import_images ./image-server/images`
- **Config:** `IMAGE_BASE_URL` (dev `http://localhost:8000`, prod `https://images.example.com`) in `Tourism/.env`
- **Dataset:** never committed — lives outside Git (shared drive / rsync); see docs.
